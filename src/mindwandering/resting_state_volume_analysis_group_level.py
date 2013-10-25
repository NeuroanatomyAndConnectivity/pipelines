import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl
import os
import pandas as pd
from CPAC.group_analysis.group_analysis import create_group_analysis

dropbox_root = "/scr/adenauer1/PowerFolder/Dropbox"
regressors_file = dropbox_root + "/papers/neural_correlates_of_mind_wandering/regressors.csv"

from variables import workingdir, resultsdir, subjects

derivatives = {
                "reho": "reho_z/_subject_id_%s/*.nii.gz",
#                "alff": "alff_z/_subject_id_%s/*.nii.gz",
                "falff": "falff_z/_subject_id_%s/*.nii.gz",
#                 "left_pcc": "seed_based_z/_roi_-8.-56.26/_subject_id_%s/*.nii.gz",
#                 "right_pcc": "seed_based_z/_roi_8.-56.26/_subject_id_%s/*.nii.gz",
#                 "left_mpfc": "seed_based_z/_roi_-6.52.-2/_subject_id_%s/*.nii.gz",
#                 "right_mpfc": "seed_based_z/_roi_6.52.-2/_subject_id_%s/*.nii.gz",
                "centrality": "degree_centrality/_subject_id_%s/_z_score0/*.nii.gz",
#                  "falff_neg_past_c96": "post_hoc_seed_based_z/_seed_name_falff_neg_past_c96/_subject_id_%s/corr_map_calc.nii.gz", 
#                  "falff_neg_words_c70": "post_hoc_seed_based_z/_seed_name_falff_neg_words_c70/_subject_id_%s/corr_map_calc.nii.gz", 
#                  "falff_pos_negative_c81": "post_hoc_seed_based_z/_seed_name_falff_pos_negative_c81/_subject_id_%s/corr_map_calc.nii.gz", 
#                  "reho_pos_friends_c93": "post_hoc_seed_based_z/_seed_name_reho_pos_friends_c93/_subject_id_%s/corr_map_calc.nii.gz", 
#                  "falff_neg_positive_c90": "post_hoc_seed_based_z/_seed_name_falff_neg_positive_c90/_subject_id_%s/corr_map_calc.nii.gz", 
#                  "falff_neg_words_c71": "post_hoc_seed_based_z/_seed_name_falff_neg_words_c71/_subject_id_%s/corr_map_calc.nii.gz", 
#                  "falff_pos_positive_c101": "post_hoc_seed_based_z/_seed_name_falff_pos_positive_c101/_subject_id_%s/corr_map_calc.nii.gz", 
#                  "reho_pos_specific_vague_c82": "post_hoc_seed_based_z/_seed_name_reho_pos_specific_vague_c82/_subject_id_%s/corr_map_calc.nii.gz",
#                  "falff_neg_specific_vague_c71": "post_hoc_seed_based_z/_seed_name_falff_neg_specific_vague_c71/_subject_id_%s/corr_map_calc.nii.gz",
#                  "falff_pos_friends_c83": "post_hoc_seed_based_z/_seed_name_falff_pos_friends_c83/_subject_id_%s/corr_map_calc.nii.gz",
#                  "reho_neg_future_c73": "post_hoc_seed_based_z/_seed_name_reho_neg_future_c73/_subject_id_%s/corr_map_calc.nii.gz",
#                  "falff_neg_words_c70_and_c71": "post_hoc_seed_based_z/_seed_name_falff_neg_words_c70/_subject_id_%s/corr_map_calc.nii.gz", 
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
    regressors_df["male"] = (regressors_df["sex"] == "male")*1
    regressors_df["female"] = (regressors_df["sex"] == "female")*1
    for reg in ["past", "future", "positive", "negative", "friends", "specific_vague", "words", "images", "firstSum", "secondSum", "age"]:
        regressors_df["male_"+reg] = (regressors_df["sex"] == "male")*regressors_df[reg]
        regressors_df["female_"+reg] = (regressors_df["sex"] == "female")*regressors_df[reg]
    
    """ First part """
    models = {
            "all": {"variables": ["past", "future", "positive", "negative", "friends", "specific_vague", "words", "images","age", "male", "female"],
                           "contrasts": [
                                         ("pos_past", 'T', ["past"], [1]),
                                         ("neg_past", 'T', ["past"], [-1]),
                                         ("pos_future", 'T', ["future"], [1]),
                                         ("neg_future", 'T', ["future"], [-1]),
                                         ("past_higher_than_future", 'T', ["past", "future"], [1, -1]),
                                         ("future_higher_than_past", 'T', ["future", "past"], [1, -1]),
                                         ("pos_positive", 'T', ["positive"], [1]),
                                         ("neg_positive", 'T', ["positive"], [-1]),
                                         ("pos_negative", 'T', ["negative"], [1]),
                                         ("neg_negative", 'T', ["negative"], [-1]),
                                         ("positive_higher_than_negative", 'T', ["positive", "negative"], [1, -1]),
                                         ("negative_higher_than_positive", 'T', ["negative", "positive"], [1, -1]),
                                         ("pos_friends", 'T', ["friends"], [1]),
                                         ("neg_friends", 'T', ["friends"], [-1]),
                                         ("pos_specific_vague", 'T', ["specific_vague"], [1]),
                                         ("neg_specific_vague", 'T', ["specific_vague"], [-1]),
                                         ("pos_words", 'T', ["words"], [1]),
                                         ("neg_words", 'T', ["words"], [-1]),
                                         ("pos_images", 'T', ["images"], [1]),
                                         ("neg_images", 'T', ["images"], [-1]),
#                                          ("pos_age", 'T', ["age"], [1]),
#                                          ("neg_age", 'T', ["age"], [-1]),
#                                          ("male_higher_than_female", 'T', ["male", "female"], [1, -1]),
#                                          ("female_higher_than_male", 'T', ["male", "female"], [-1, 1]),
                                        ]},
#               "age_sex": {"variables": ["age", "male", "female"],
#                            "contrasts": [("pos_age", 'T', ["age"], [1]),
#                                          ("neg_age", 'T', ["age"], [-1]),
#                                          ("male_higher_than_female", 'T', ["male", "female"], [1, -1]),
#                                          ("female_higher_than_male", 'T', ["male", "female"], [-1, 1]),
#                                         ]},
            "first_sum": {"variables": ["firstSum", "age", "male", "female"],
                         "contrasts": [("pos_firstSum", 'T', ["firstSum"], [1]),
                                       ("neg_firstSum", 'T', ["firstSum"], [-1]),
                                      ]}
                }
    for name, model in models.iteritems():
        model_node = pe.Node(fsl.MultipleRegressDesign(), name="%s_model"%name)
        regressors = {}
        for reg in model["variables"]:
            regressors[reg] = list(regressors_df[reg])
        model_node.inputs.regressors = regressors
        model_node.inputs.contrasts = model["contrasts"]
        model_nodes[name] = model_node
        
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
#                  ("neg_age", 'T', ["age"], [-1]),base + "_z_map.nii.gz"
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
        
        def one_sample_test(avg_file, stddev_file, n):
            import nibabel as nb
            import numpy as np
            import scipy.stats as stats
            import os
            from nipype.utils.filemanip import split_filename
            
            avg_nii = nb.load(avg_file)
            avg_data = avg_nii.get_data()
            stddev_nii = nb.load(stddev_file)
            stddev_data = stddev_nii.get_data()
            
            t_map = (avg_data/(stddev_data/np.sqrt(n)))
            
            z_map = stats.norm.ppf(stats.t.cdf(t_map,n-1))
            z_map[np.isinf(z_map)] = t_map[np.isinf(z_map)]
            
            
            out_nii = nb.Nifti1Image(z_map, avg_nii.get_affine(), avg_nii.get_header())
            _, base, _ = split_filename(avg_file)
            
            nb.save(out_nii, base + "_z_map.nii.gz")
            
            return os.path.abspath(base + "_z_map.nii.gz")
        
        one_sample_t_test = pe.Node(util.Function(input_names= ["avg_file", "stddev_file", "n"],
                                                  output_names = ["z_map"],
                                                  function = one_sample_test), 
                                    name="%s_one_sample_t_test"%derivative)
        one_sample_t_test.inputs.n = len(subjects) - 1
        wf.connect(avg, "out_file", one_sample_t_test, "avg_file")
        wf.connect(stddev, "out_file", one_sample_t_test, "stddev_file")
        
        for model in model_nodes.keys():
#             estimate = pe.Node(fsl.Randomise(), name="%s_%s_estimate"%(model,derivative))
#             estimate.inputs.tfce = True
#             estimate.inputs.raw_stats_imgs = True
#             estimate.inputs.vox_p_values = True
#             estimate.inputs.demean = True
#             estimate.inputs.base_name = "%s_%s"%(model,derivative)
#             wf.connect(merge, "merged_file", estimate, "in_file")
#             if derivative != "centrality":
#                 wf.connect(restrict_to_grey, "out_file", estimate, "mask")
#             wf.connect(model_nodes[model], "design_mat", estimate, "design_mat")
#             wf.connect(model_nodes[model], "design_con", estimate, "tcon")
#             wf.connect(model_nodes[model], "design_fts", estimate, "fcon")
            
            estimate_parametric = create_group_analysis(wf_name="%s_%s_estimate_parametric"%(model,derivative))
            estimate_parametric.inputs.inputspec.z_threshold = 2.3
            estimate_parametric.inputs.inputspec.p_threshold = 1 #0.05/2.0/4.0
            estimate_parametric.inputs.inputspec.parameters = ("/scr/adenauer1/templates/", "MNI152")
            merge_mask = estimate_parametric.get_node("merge_mask")
            cluster = estimate_parametric.get_node("easy_thresh_z").get_node("cluster")
            cluster.inputs.use_mm = True
            estimate_parametric.remove_nodes([merge_mask])
            estimate_parametric.remove_nodes([estimate_parametric.get_node("easy_thresh_z").get_node("overlay"),
                                              estimate_parametric.get_node("easy_thresh_z").get_node("slicer"),
                                              estimate_parametric.get_node("easy_thresh_z").get_node("create_tuple"),
                                              estimate_parametric.get_node("easy_thresh_z").get_node("image_stats"),
                                              estimate_parametric.get_node("easy_thresh_z").get_node("get_backgroundimage2")])
            if derivative != "centrality":
                wf.connect(restrict_to_grey, "out_file", estimate_parametric, "fsl_flameo.mask_file")
                wf.connect(restrict_to_grey, "out_file", estimate_parametric, "easy_thresh_z.inputspec.merge_mask")
            else:
                estimate_parametric.inputs.fsl_flameo.mask_file = "/scr/kalifornien1/mindwandering/workingdir/calculating_measures/downsample_mask/group_mask_masked_flirt.nii.gz"
                estimate_parametric.inputs.easy_thresh_z.inputspec.merge_mask = "/scr/kalifornien1/mindwandering/workingdir/calculating_measures/downsample_mask/group_mask_masked_flirt.nii.gz"


            estimate_parametric.inputs.easy_thresh_z.cluster.out_threshold_file = [ "derivative_" + derivative + "_model_" + model + "_contrast_" + c[0] + ".nii.gz" for c in models[model]["contrasts"]]
            wf.connect(derivative_datasource, "derivative_files", estimate_parametric, "inputspec.zmap_files")
            wf.connect(model_nodes[model], "design_mat", estimate_parametric, "inputspec.mat_file")
            wf.connect(model_nodes[model], "design_con", estimate_parametric, "inputspec.con_file")
            wf.connect(model_nodes[model], "design_fts", estimate_parametric, "inputspec.fts_file")
            wf.connect(model_nodes[model], "design_grp", estimate_parametric, "inputspec.grp_file")
            
    
    #wf.write_graph(graph2use='exec')
    wf.run(plugin="MultiProc")
    
    
# for file in glob("/scr/kalifornien1/mindwandering/workingdir/group_analysis/*estimate/*tfce_corrp_tstat*.nii.gz"):
#     max = nb.load(file).get_data().max()
#     if max > 0.95:
#         print file.split("/")[-1] + " max p:" + str(max)

