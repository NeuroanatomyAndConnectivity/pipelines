import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl
import os
import pandas as pd
dropbox_root = "/scr/adenauer1/PowerFolder/Dropbox"
regressors_file = dropbox_root + "/papers/neural_correlates_of_mind_wandering/regressors.csv"

from variables import workingdir, resultsdir, subjects

derivatives = {
#                "reho": "reho_z/_subject_id_%s/*.nii.gz",
#                "alff": "alff_z/_subject_id_%s/*.nii.gz",
#                "falff": "falff_z/_subject_id_%s/*.nii.gz",
#                "left_pcc": "seed_based_z/_roi_-8.-56.26/_subject_id_%s/*.nii.gz",
#                "right_pcc": "seed_based_z/_roi_8.-56.26/_subject_id_%s/*.nii.gz",
               "left_mpfc": "seed_based_z/_roi_-6.52.-2/_subject_id_%s/*.nii.gz",
#                "right_mpfc": "seed_based_z/_roi_6.52.-2/_subject_id_%s/*.nii.gz",
#                "centrality": "degree_centrality/_subject_id_%s/*.nii",
               }

# for i, RSNid in enumerate([5, 15, 9, 6, 8, 1, 2, 7, 12, 11]):
#     derivatives["RSN%d"%(i+1)] = "dual_regression_z/_subject_id_%s" + "/temp_reg_map_z_%04d.nii.gz"%RSNid

if __name__ == '__main__':
    wf = pe.Workflow(name="group_analysis")
    wf.base_dir = workingdir
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
    
    mask_datasource = pe.Node(nio.DataGrabber(infields=['subject_ids'], outfields = ['mask_files']), name="mask_datasource")
    mask_datasource.inputs.base_directory = resultsdir
    mask_datasource.inputs.template = 'functional_mask/_subject_id_%s/*.nii'
    mask_datasource.inputs.template_args['mask_files'] = [['subject_ids']]
    mask_datasource.inputs.sort_filelist = True
    mask_datasource.inputs.subject_ids = subjects
    
    def calculate_group_mask(list_of_subject_masks):
        import nibabel as nb
        import numpy as np
        import os
        first_nii = nb.load(list_of_subject_masks[0])
        sum_mask = np.zeros(first_nii.get_shape())
        for mask in list_of_subject_masks:
            mask_data = nb.load(mask).get_data()
            sum_mask[np.logical_and(np.logical_not(np.isnan(mask_data)),mask_data > 0)] += 1
        sum_mask /= len(list_of_subject_masks)
        sum_mask[sum_mask != 1] = 0
        new_img = nb.Nifti1Image(sum_mask, first_nii.get_affine(), first_nii.get_header())
        filename= "group_mask.nii.gz"
        nb.save(new_img, filename)
        return os.path.abspath(filename)
    
    calculate_group_mask_node = pe.Node(util.Function(input_names=["list_of_subject_masks"], 
                                                      output_names=["group_mask"], 
                                                      function=calculate_group_mask), 
                                        name="calculate_group_mask")
    wf.connect(mask_datasource, "mask_files", calculate_group_mask_node, "list_of_subject_masks")
    
    restrict_to_grey = pe.Node(fsl.maths.ApplyMask(), name="restrict_to_grey")
    restrict_to_grey.inputs.mask_file = "/scr/adenauer1/MNI152_T1_graymatter100.nii.gz"
    wf.connect(calculate_group_mask_node, "group_mask", restrict_to_grey, "in_file")
    
#     merge_masks = pe.Node(fsl.Merge(dimension="t"), name="merge_masks")
#     wf.connect(mask_datasource, "mask_files", merge_masks, "in_files")
#     
#     smooth_masks = pe.Node(fsl.maths.IsotropicSmooth(fwhm=fwhm), name="smooth_masks")
#     wf.connect(merge_masks, "merged_file", smooth_masks, "in_file")
#     
#     mask_smooth_masks = pe.Node(fsl.maths.ApplyMask(), name="mask_smooth_masks")
#     wf.connect(smooth_masks, "out_file", mask_smooth_masks, "in_file")
#     wf.connect(merge_masks, "merged_file", mask_smooth_masks, "mask_file")
    
#     def create_design(regressors_file, regressors, confounds=[], subject_ids=None):
#         
#         regressors_df = pd.read_csv(regressors_file).sort(columns="queried_ursi")
#         if subject_ids:
#             regressors_df = regressors_df[regressors_df.queried_ursi.isin(subject_ids)]
#         regressors_df = regressors_df.filter(regressors + confounds)
#         for row in regressors_df.iterrows():
#             print "\t".join([str(i) for i in row[1]])
#         
#         for i,regressor in enumerate(regressors):
#             print "/ContrastName%d\t%s"(i,regressor)
#             
#         print """/NumWaves    %d
# /NumContrasts    %d
# """%(len(regressors + confounds), len(regressors))
#         
#         for i,regressor in enumerate(regressors):
#             print ["0"]*len(confounds)
            
    models = ["past", "future", "positive", "negative", "friends", "specific_vague", "words", "images", "firstSum", "secondSum"]
    #models = ["firstSum"]
    model_nodes = {}       
    confounds = ["age","sex"]
    
    regressors_df = pd.read_csv(regressors_file).sort(columns="queried_ursi")
    subjects_int = [int(s) for s in subjects]
    regressors_df = regressors_df[regressors_df.queried_ursi.isin(subjects_int)]
    
    """ First part """
    variables = ["past", "future", "positive", "negative", "friends"]
    contrasts = [(("pos_past_no_counfounds_full_model", 'T', ["past"], [1]), ["past", "future", "positive", "negative", "friends"]),
                 (("neg_past_no_counfounds_full_model", 'T', ["past"], [-1]), ["past", "future", "positive", "negative", "friends"]),
                 (("pos_past_age_sex_counfounds_full_model", 'T', ["past"], [1]), ["age", "sex", "past", "future", "positive", "negative", "friends"]),
                 (("neg_past_age_sex_counfounds_full_model", 'T', ["past"], [-1]), ["age", "sex", "past", "future", "positive", "negative", "friends"]),
                 (("pos_past", 'T', ["past"], [1]), ["past"]),
                 (("neg_past", 'T', ["past"], [-1]), ["past"]),
#                  ("pos_future", 'T', ["future"], [1]),
#                  ("neg_future", 'T', ["future"], [-1]),
#                  ("past_vs_future", 'T', ["past", "future"], [1, -1]),
#                  ("future_vs_past", 'T', ["future", "past"], [1, -1]),
#                  ("pos_positive", 'T', ["positive"], [1]),
#                  ("pos_negative", 'T', ["negative"], [1]),
#                  ("neg_positive", 'T', ["positive"], [-1]),
#                  ("neg_negative", 'T', ["negative"], [-1]),
#                  ("positive_vs_negative", 'T', ["positive", "negative"], [1, -1]),
#                  ("negative_vs_positive", 'T', ["negative", "positive"], [1, -1]),
#                  ("pos_friends", 'T', ["friends"], [1]),
#                  ("neg_friends", 'T', ["friends"], [-1]),
                 ]
    for contrast in contrasts:
        model_node = pe.Node(fsl.MultipleRegressDesign(), name="%s_model"%contrast[0][0])
        regressors = {}
        for reg in contrast[1]:
            regressors[reg] = list(regressors_df[reg])
        model_node.inputs.regressors = regressors
        model_node.inputs.contrasts = [contrast[0]]
        model_nodes[contrast[0][0]] = model_node
        
#     first_part_model_node = pe.Node(fsl.MultipleRegressDesign(), name="first_part_model")
#     regressors = {}
#     for reg in confounds + ["past", "future", "positive", "negative", "friends"]:
#         regressors[reg] = list(regressors_df[reg])
#     past = ("past", 'T', ["past"], [1])
#     future = ("future", 'T', ["future"], [1])
#     past_vs_future = ("past_vs_future", 'T', ["past", "future"], [1, -1])
#     future_vs_past = ("future_vs_past", 'T', ["future", "past"], [1, -1])
#     positive = ("positive", 'T', ["positive"], [1])
#     negative = ("negative", 'T', ["negative"], [1])
#     positive_vs_negative = ("positive_vs_negative", 'T', ["positive", "negative"], [1, -1])
#     negative_vs_positive = ("negative_vs_positive", 'T', ["negative", "positive"], [1, -1])
#     friends = ("friends", 'T', ["friends"], [1])
#     contrasts = [past, future, positive, negative, friends, past_vs_future, future_vs_past, positive_vs_negative, negative_vs_positive,
#                 ("first_part", 'F', [past, future, positive, negative, friends])]
#     first_part_model_node.inputs.regressors = regressors
#     first_part_model_node.inputs.contrasts = contrasts
#     model_nodes["first_part"] = first_part_model_node
#     
#     second_part_model_node = pe.Node(fsl.MultipleRegressDesign(), name="second_part_model")
#     regressors = {}
#     for reg in confounds + [ "specific_vague", "words", "images"]:
#         regressors[reg] = list(regressors_df[reg])
#     specific_vague = ("specific_vague", 'T', ["specific_vague"], [1])
#     words = ("words", 'T', ["words"], [1])
#     images = ("images", 'T', ["images"], [1])
#     contrasts = [specific_vague, words, images,
#                 ("second_part", 'F', [specific_vague, words, images])]
#     second_part_model_node.inputs.regressors = regressors
#     second_part_model_node.inputs.contrasts = contrasts
#     model_nodes["second_part"] = second_part_model_node
#     
#     age_model_node = pe.Node(fsl.MultipleRegressDesign(), name="age_model_node")
#     regressors = {}
#     regressors["age"] = list(regressors_df["age"])
#     regressors["sex"] = list(regressors_df["sex"])
#     contrasts = [("pos_age", 'T', ["age"], [1]),
#                  ("neg_age", 'T', ["age"], [-1]),
#                  ("pos_sex", 'T', ["sex"], [1]),
#                  ("neg_sex", 'T', ["sex"], [-1])]
#     age_model_node.inputs.regressors = regressors
#     age_model_node.inputs.contrasts = contrasts
#     model_nodes["age"] = age_model_node
    
    
    for derivative, template in derivatives.iteritems():
        derivative_datasource = pe.Node(nio.DataGrabber(infields=['subject_ids'], outfields = ['derivative_files']), name="%s_datasource"%derivative)
        derivative_datasource.inputs.base_directory = resultsdir
        derivative_datasource.inputs.template = template
        derivative_datasource.inputs.sort_filelist = True
        derivative_datasource.inputs.subject_ids = subjects
        
        merge = pe.Node(fsl.Merge(dimension="t"), name="%s_merge"%derivative)
        wf.connect(derivative_datasource, "derivative_files", merge, "in_files")
        
        avg = pe.Node(fsl.maths.MeanImage(dimension="T"), name="%s_avg"%derivative)
        avg.inputs.out_file = "%s_avg.nii.gz"%derivative
        wf.connect(merge, "merged_file", avg, "in_file")
        
        stddev = pe.Node(fsl.ImageMaths(op_string="-Tstd"), name="%s_stddev"%derivative)
        stddev.inputs.out_file = "%s_stddev.nii.gz"%derivative
        wf.connect(merge, "merged_file", stddev, "in_file")
        
        for model in model_nodes.keys():
            estimate = pe.Node(fsl.Randomise(), name="%s_%s_estimate"%(model,derivative))
            estimate.inputs.tfce = True
            estimate.inputs.raw_stats_imgs = True
            estimate.inputs.vox_p_values = True
            estimate.inputs.demean = True
            estimate.inputs.base_name = "%s_%s"%(model,derivative)
            wf.connect(merge, "merged_file", estimate, "in_file")
            if derivative != "centrality":
                wf.connect(restrict_to_grey, "out_file", estimate, "mask")
            wf.connect(model_nodes[model], "design_mat", estimate, "design_mat")
            wf.connect(model_nodes[model], "design_con", estimate, "tcon")
            wf.connect(model_nodes[model], "design_fts", estimate, "fcon")
    
    #wf.write_graph(graph2use='exec')
    wf.run(plugin="CondorDAGMan")
    
    
# for file in glob("/scr/kalifornien1/mindwandering/workingdir/group_analysis/*estimate/*tfce_corrp_tstat*.nii.gz"):
#     max = nb.load(file).get_data().max()
#     if max > 0.95:
#         print file.split("/")[-1] + " max p:" + str(max)

