import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
import nipype.interfaces.fsl as fsl
import os
from variables import resultsdir, subjects, workingdir, rois

if __name__ == '__main__':
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(workingdir, "rs_analysis_group")
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
    
    struct_datasource = pe.Node(nio.DataGrabber(infields=['subject_ids'], outfields = ['normalized_T1s']), name="struct_datasource")
    struct_datasource.inputs.base_directory = os.path.join(resultsdir,'volumes')
    struct_datasource.inputs.template = 'normalized_T1/_subject_id_%s/*.nii.gz'
    struct_datasource.inputs.template_args['normalized_T1s'] = [['subject_ids']]
    struct_datasource.inputs.sort_filelist = True
    struct_datasource.inputs.subject_ids = subjects
    
    merge_structs = pe.Node(fsl.Merge(dimension='t'), name="merge_structs")
    
    wf.connect(struct_datasource, 'normalized_T1s', merge_structs, 'in_files')
    
    mean_struct = pe.Node(fsl.MeanImage(dimension="T"), name="mean_struct")
    
    wf.connect(merge_structs, 'merged_file', mean_struct, 'in_file')
    
    std_struct = pe.Node(fsl.ImageMaths(op_string = "-Tstd"),name="std_struct")
    
    wf.connect(merge_structs, 'merged_file', std_struct, 'in_file')
    ds = pe.Node(nio.DataSink(), name="datasink")
    ds.run_without_submitting = True
    ds.inputs.regexp_substitutions=[("_diff_i[^/]*/", ""),
                                    ("_avg_i[^/]*/", "")]
    ds.inputs.base_directory = os.path.join(resultsdir, "volumes")
    
    wf.connect(mean_struct, 'out_file', ds, "mean_struct")
    wf.connect(std_struct, 'out_file', ds, "std_struct")
    
    def format_roi(roi_str):
        import string
        valid_chars = "-_.%s%s" % (string.ascii_letters, string.digits)
        return ''.join(c for c in str(roi_str).replace(",","_") if c in valid_chars)
    
    for roi in rois:
        suffix = "_" + format_roi(roi)
    
        func_datasource = pe.Node(nio.DataGrabber(infields=['subject_ids', 'roi'], outfields = ['connectivity_maps']), name="func_datasource"+suffix)
        func_datasource.inputs.base_directory = os.path.join(resultsdir,'volumes')
        func_datasource.inputs.template = 'normalized_z_scored_corr_map/_subject_id_%s/_roi_*/_bandpass_highpass_freq_0.01_lowpass_freq_0.1/_fwhm_5/roi_%s_masked.nii'
        func_datasource.inputs.sort_filelist = True
        func_datasource.inputs.subject_ids = subjects
        func_datasource.inputs.roi = format_roi(roi)
        
        merge_conn_maps = pe.Node(fsl.Merge(dimension='t'), name="merge_conn_maps"+suffix)
        
        wf.connect(func_datasource, 'connectivity_maps', merge_conn_maps, 'in_files')
        
        mean_conn_map = pe.Node(fsl.MeanImage(dimension="T"), name="mean_conn_map"+suffix)
        
        wf.connect(merge_conn_maps, 'merged_file', mean_conn_map, 'in_file')
        
        std_conn_maps = pe.Node(fsl.ImageMaths(op_string = "-Tstd", suffix="_std"),name="std_conn_maps"+suffix)
        
        wf.connect(merge_conn_maps, 'merged_file', std_conn_maps, 'in_file')

        wf.connect(mean_conn_map, 'out_file', ds, "mean_conn_maps"+suffix)
        wf.connect(std_conn_maps, 'out_file', ds, "std_conn_maps"+suffix)
    
    for roi1 in rois:
        for roi2 in [roi for roi in rois if roi is not roi1]:
            suffix = "_" + format_roi(roi1) + "_vs_" + format_roi(roi2)
            
            diff_i = pe.MapNode(fsl.maths.BinaryMaths(), name="diff_i"+suffix, iterfield=["in_file", "operand_file", "out_file"])
            diff_i.inputs.out_file = [s+".nii" for s in subjects]
            diff_i.inputs.operation = "sub"
            diff_i.inputs.output_type = "NIFTI"
            ds1 = wf.get_node("func_datasource_"+format_roi(roi1))
            wf.connect(ds1, "connectivity_maps", diff_i, "in_file")
            ds2 = wf.get_node("func_datasource_"+format_roi(roi2))
            wf.connect(ds2, "connectivity_maps", diff_i, "operand_file")
            wf.connect(diff_i, 'out_file', ds, "diff_files"+suffix)
            
            avg_i = pe.MapNode(fsl.maths.MultiImageMaths(), name="avg_i"+suffix, iterfield=["in_file", "operand_files", "out_file"])
            avg_i.inputs.out_file = [s+".nii" for s in subjects]
            avg_i.inputs.op_string = "-add %s -div 2"
            avg_i.inputs.output_type = "NIFTI"
            ds1 = wf.get_node("func_datasource_"+format_roi(roi1))
            wf.connect(ds1, "connectivity_maps", avg_i, "in_file")
            ds2 = wf.get_node("func_datasource_"+format_roi(roi2))
            wf.connect(ds2, "connectivity_maps", avg_i, "operand_files")
            wf.connect(avg_i, 'out_file', ds, "avg_files"+suffix)
            
            diff = pe.Node(fsl.maths.BinaryMaths(), name="diff"+suffix)
            diff.inputs.operation = "sub"
            merge1 = wf.get_node("merge_conn_maps"+"_"+format_roi(roi1))
            wf.connect(merge1, "merged_file", diff, "in_file")
            merge2 = wf.get_node("merge_conn_maps"+"_"+format_roi(roi2))
            wf.connect(merge2, "merged_file", diff, "operand_file")
            
#            onesample_t_test = pe.Node(fsl.Randomise(), name="onesample_t_test" + suffix)
#            onesample_t_test.inputs.base_name = suffix
#            onesample_t_test.inputs.tfce = True
#            onesample_t_test.inputs.mask = fsl.Info.standard_image("MNI152_T1_2mm_brain_mask.nii.gz")
#            onesample_t_test.inputs.one_sample_group_mean = True
#            wf.connect(diff, "out_file", onesample_t_test, "in_file")
#            wf.connect(onesample_t_test, 't_corrected_p_files', ds, "p_map"+suffix)

            
#    func_datasource = pe.Node(nio.DataGrabber(infields=['subject_id', 'roi'], outfields = ['connectivity_maps']), name="func_datasource")
#    func_datasource.inputs.base_directory = os.path.join(resultsdir,'volumes')
#    func_datasource.inputs.template = 'normalized_z_scored_corr_map/_subject_id_%s/_roi_*/_fwhm_5/roi_%s_masked.nii'
#    func_datasource.inputs.template_args['normalized_T1s'] = [['subject_ids', 'roi']]
#    func_datasource.inputs.sort_filelist = True
#    func_datasource.iterfields = [('subject_id', subjects)]
#    
#    roi_infosource = pe.Node(util.IdentityInterface(fields=["roi"]), name="roi_infosource")
#    roi_infosource.iterables = ('roi', rois)
#    wf.connect(roi_infosource, ("roi", format_roi), func_datasource, "roi")

    
    wf.run(plugin="Linear", plugin_args={'n_procs':4})
