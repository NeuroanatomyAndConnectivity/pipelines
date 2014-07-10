import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
import nipype.interfaces.utility as util
import nipype.interfaces.afni as afni

from variables import workingdir, resultsdir, subjects

if __name__ == '__main__':
    
    afni.base.AFNICommand.set_default_output_type("NIFTI")
    
    wf = pe.Workflow(name="post_hoc_seeds")
    wf.base_dir = workingdir
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
    
    ds = pe.Node(nio.DataSink(), name="datasink")
    ds.run_without_submitting = True
    ds.inputs.base_directory = resultsdir
    
    subjects_infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']), name="subjects_infosource")
    subjects_infosource.iterables = ("subject_id", subjects)
    
    datasource = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields = ['EPI_bandpassed', "EPI_full_spectrum"]), name="datasource")
    datasource.inputs.base_directory = "/scr/kalifornien1/mindwandering/results/"
    datasource.inputs.template = '%s/smri/warped_image/fwhm_6.0/*_afni_%s_wtsimt.nii.gz'
    datasource.inputs.template_args['EPI_bandpassed'] = [['subject_id', "bandpassed"]]
    datasource.inputs.template_args['EPI_full_spectrum'] = [['subject_id', "fullspectrum"]]
    datasource.inputs.sort_filelist = True
    wf.connect(subjects_infosource, "subject_id", datasource, "subject_id")
    
    post_hoc_seed_infosource = pe.Node(util.IdentityInterface(fields=["seed_name"]), name="post_hoc_seed_infosource")
    post_hoc_seed_infosource.iterables = ('seed_name', [
                                                        "all_with_MeanFD_falff_neg_past_c97",      "all_with_MeanFD_falff_neg_words_c75" ,   "all_with_MeanFD_falff_pos_negative_c81",
                                                        "all_with_MeanFD_reho_pos_friends_c92",'all_with_MeanFD_falff_neg_positive_c88',"all_with_MeanFD_falff_pos_friends_c84",  
                                                        "all_with_MeanFD_falff_pos_positive_c98",  "all_with_MeanFD_reho_pos_specific_vague_c78",
                                                        'all_with_MeanFD_falff_neg_words_c74_and_c75', 'all_with_MeanFD_falff_pos_images_c88',   
                                                        'all_with_MeanFD_reho_neg_future_c75',
                                                        'all_with_MeanFD_falff_past_higher_than_future_c76','all_with_MeanFD_falff_neg_friends_c82',
                                                        'all_with_MeanFD_falff_neg_specific_vague_c77','all_with_MeanFD_centrality_neg_past_c26_2mm',
                                                        'all_with_MeanFD_reho_neg_negative_c87','all_with_MeanFD_reho_positive_higher_than_negative_c75',
                ])
    
    seed_datasource = pe.Node(nio.DataGrabber(infields=['seed_name'], outfields = ['seed_mask']), name="seed_datasource")
    seed_datasource.inputs.base_directory = "/scr/adenauer1/PowerFolder/Dropbox/papers/neural_correlates_of_mind_wandering/post_hoc_seeds/"
    seed_datasource.inputs.template = '%s.nii.gz'
    seed_datasource.inputs.sort_filelist = True
    wf.connect(post_hoc_seed_infosource, "seed_name", seed_datasource, "seed_name")
    
    extract_timeseries = pe.Node(afni.Maskave(), name="extract_timeseries")
    extract_timeseries.inputs.quiet = True
    wf.connect(seed_datasource, "seed_mask", extract_timeseries, "mask")
    wf.connect(datasource, "EPI_bandpassed", extract_timeseries, "in_file")
    
    correlation_map = pe.Node(afni.Fim(), name="correlation_map")
    correlation_map.inputs.out = "Correlation"
    correlation_map.inputs.outputtype = "NIFTI"
    correlation_map.inputs.out_file = "corr_map.nii"
    wf.connect(extract_timeseries, "out_file", correlation_map, "ideal_file")
    wf.connect(datasource, "EPI_bandpassed", correlation_map, "in_file")
    
    z_trans = pe.Node(interface=afni.Calc(), name='z_trans')
    z_trans.inputs.expr = 'log((1+a)/(1-a))/2'
    z_trans.inputs.outputtype = 'NIFTI_GZ'
    wf.connect(correlation_map, "out_file", z_trans, "in_file_a")
    wf.connect(z_trans, 'out_file', ds, "post_hoc_seed_based_z")

    wf.run(plugin="Linear")


