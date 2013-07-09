import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl
import os
import pandas as pd
dropbox_root = "/scr/adenauer1/PowerFolder/Dropbox"

workingdir = "/scr/adenauer1//mindwandering_workign_dir"
datadir = dropbox_root + "/papers/neural_correlates_of_mind_wandering/neuro_data"
regressors_file = dropbox_root + "/papers/neural_correlates_of_mind_wandering/regressors.csv"

derivatives = ["alff", "falff", "PCC_map", "aMPFC_map", "reho"]

fwhm = 6

subjects = sorted([102157,
 103645,
 105488,
 106780,
 108355,
 109727,
 111282,
 112249,
 112828,
 113013,
 114232,
 115321,
 115454,
 115564,
 115824,
 116039,
 116065,
 116834,
 116842,
 117168,
 118051,
 119866,
 120557,
 122169,
 122512,
 122816,
 122844,
 123173,
 123429,
 123971,
 125762,
 126919,
 131127,
 131832,
 132717,
 #132850, missing data
 132995,
 134795,
 135671,
 136303,
 136416,
 137073,
 137496,
 137679,
 139212,
 139300,
 139480,
 141795,
 142673,
 144667,
 144702,
 146714,
 146865,
 147122,
 150404,
 150525,
 150589,
 152968,
 153114,
 154423,
 155419,
 155458,
 156263,
 156678,
 158411,
 158560,
 158744,
 159429,
 161200,
 162251,
 162704,
 162902,
 163228,
 163508,
 164900,
 166094,
 166987,
 167827,
 168239,
 168357,
 168413,
 168489,
 169007,
 173085,
 173286,
 173358,
 173496,
 174363,
 174886,
 177330,
 177857,
 178174,
 178453,
 179005,
 179873,
 180308,
 182376,
 182604,
 183457,
 183726,
 185428,
 185676,
 185781,
 186067,
 186277,
 187635,
 188199,
 188219,
 188854,
 189478,
 190501,
 194023,
 194956,
 195031,
 195236,
 196651,
 197836,
 198051,
 198130,
 198357,
 199340,
 199620])

if __name__ == '__main__':
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(workingdir, "rs_analysis_group")
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
    
    mask_datasource = pe.Node(nio.DataGrabber(infields=['subject_ids'], outfields = ['mask_files']), name="mask_datasource")
    mask_datasource.inputs.base_directory = datadir
    mask_datasource.inputs.template = 'functional_mask/%07d.nii.gz'
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
    restrict_to_grey.inputs.mask_file = "/scr/adenauer1/3mm_grey.nii.gz"
    wf.connect(calculate_group_mask_node, "group_mask", restrict_to_grey, "in_file")
    
    merge_masks = pe.Node(fsl.Merge(dimension="t"), name="merge_masks")
    wf.connect(mask_datasource, "mask_files", merge_masks, "in_files")
    
    smooth_masks = pe.Node(fsl.maths.IsotropicSmooth(fwhm=fwhm), name="smooth_masks")
    wf.connect(merge_masks, "merged_file", smooth_masks, "in_file")
    
    mask_smooth_masks = pe.Node(fsl.maths.ApplyMask(), name="mask_smooth_masks")
    wf.connect(smooth_masks, "out_file", mask_smooth_masks, "in_file")
    wf.connect(merge_masks, "merged_file", mask_smooth_masks, "mask_file")
    
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
    model_nodes = {}       
    confounds = ["age", "sex", "MeanFD"]
    
    regressors_df = pd.read_csv(regressors_file).sort(columns="queried_ursi")
    regressors_df = regressors_df[regressors_df.queried_ursi.isin(subjects)]
    for model in models:
        model_node = pe.Node(fsl.MultipleRegressDesign(), name="%s_model"%model)
        regressors = {}
        for reg in confounds + [model]:
            regressors[reg] = list(regressors_df[reg])
        contrasts = [("pos_"+model, 'T', [model], [1]),
                     ("neg_"+model, 'T', [model], [-1])]
        model_node.inputs.regressors = regressors
        model_node.inputs.contrasts = contrasts
        model_nodes[model] = model_node
        
    first_part_model_node = pe.Node(fsl.MultipleRegressDesign(), name="first_part_model")
    regressors = {}
    for reg in confounds + ["past", "future", "positive", "negative", "friends"]:
        regressors[reg] = list(regressors_df[reg])
    past = ("past", 'T', ["past"], [1])
    future = ("future", 'T', ["future"], [1])
    positive = ("positive", 'T', ["positive"], [1])
    negative = ("negative", 'T', ["negative"], [1])
    friends = ("friends", 'T', ["friends"], [1])
    contrasts = [past, future, positive, negative, friends,
                ("first_part", 'F', [past, future, positive, negative, friends])]
    first_part_model_node.inputs.regressors = regressors
    first_part_model_node.inputs.contrasts = contrasts
    model_nodes["first_part"] = first_part_model_node
    
    second_part_model_node = pe.Node(fsl.MultipleRegressDesign(), name="second_part_model")
    regressors = {}
    for reg in confounds + [ "specific_vague", "words", "images"]:
        regressors[reg] = list(regressors_df[reg])
    specific_vague = ("specific_vague", 'T', ["specific_vague"], [1])
    words = ("words", 'T', ["words"], [1])
    images = ("images", 'T', ["images"], [1])
    contrasts = [specific_vague, words, images,
                ("second_part", 'F', [specific_vague, words, images])]
    second_part_model_node.inputs.regressors = regressors
    second_part_model_node.inputs.contrasts = contrasts
    model_nodes["second_part"] = second_part_model_node
    
    age_model_node = pe.Node(fsl.MultipleRegressDesign(), name="age_model_node")
    regressors["age"] = list(regressors_df["age"])
    contrasts = [("pos_age", 'T', ["age"], [1]),
                 ("neg_age", 'T', ["age"], [-1])]
    age_model_node.inputs.regressors = regressors
    age_model_node.inputs.contrasts = contrasts
    model_nodes["age"] = age_model_node
    
    
    for derivative in derivatives:
        derivative_datasource = pe.Node(nio.DataGrabber(infields=['subject_ids'], outfields = ['derivative_files']), name="%s_datasource"%derivative)
        derivative_datasource.inputs.base_directory = datadir
        derivative_datasource.inputs.template = derivative + '/%07d.nii.gz'
        derivative_datasource.inputs.template_args['mask_files'] = [['subject_ids']]
        derivative_datasource.inputs.sort_filelist = True
        derivative_datasource.inputs.subject_ids = subjects
        
        merge = pe.Node(fsl.Merge(dimension="t"), name="%s_merge"%derivative)
        wf.connect(derivative_datasource, "derivative_files", merge, "in_files")
        
        smooth = pe.Node(fsl.maths.IsotropicSmooth(fwhm=fwhm), name="%s_smooth"%derivative)
        wf.connect(merge, "merged_file", smooth, "in_file")
        
        correct_for_border_effects = pe.Node(fsl.maths.BinaryMaths(operation="div"), 
                                             name="%s_correct_for_border_effects"%derivative)
        wf.connect(smooth, "out_file", correct_for_border_effects, "in_file")
        wf.connect(mask_smooth_masks, "out_file", correct_for_border_effects, "operand_file")
        
        avg = pe.Node(fsl.maths.MeanImage(dimension="T"), name="%s_avg"%derivative)
        avg.inputs.out_file = "%s_avg.nii.gz"%derivative
        wf.connect(correct_for_border_effects, "out_file", avg, "in_file")
        
        stddev = pe.Node(fsl.ImageMaths(op_string="-Tstd"), name="%s_stddev"%derivative)
        stddev.inputs.out_file = "%s_stddev.nii.gz"%derivative
        wf.connect(correct_for_border_effects, "out_file", stddev, "in_file")
        
        for model in model_nodes.keys():
            estimate = pe.Node(fsl.Randomise(), name="%s_%s_estimate"%(model,derivative))
            estimate.inputs.tfce = True
            estimate.inputs.raw_stats_imgs = True
            estimate.inputs.vox_p_values = True
            estimate.inputs.demean = True
            estimate.inputs.base_name = "%s_%s"%(model,derivative)
            wf.connect(correct_for_border_effects, "out_file", estimate, "in_file")
            wf.connect(restrict_to_grey, "out_file", estimate, "mask")
            wf.connect(model_nodes[model], "design_mat", estimate, "design_mat")
            wf.connect(model_nodes[model], "design_con", estimate, "tcon")
            wf.connect(model_nodes[model], "design_fts", estimate, "fcon")
              
            fdr = pe.MapNode(fsl.FDR(), name="%s_%s_fdr"%(model,derivative), iterfield=["p_val_image"])
            fdr.inputs.one_minus_p = True
            wf.connect(estimate, "t_p_files", fdr, "p_val_image")
    
    wf.write_graph(graph2use='exec')
    wf.run(plugin="Linear")
