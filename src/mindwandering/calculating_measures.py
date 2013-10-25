import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
from CPAC.reho import create_reho
from CPAC.alff import create_alff
from CPAC.timeseries.timeseries_analysis import get_spatial_map_timeseries
from CPAC.sca.sca import create_temporal_reg

from variables import workingdir, resultsdir, subjects, rois
from nipype.algorithms.degree_centrality import DegreeCentrality
from CPAC.network_centrality.z_score import get_zscore

if __name__ == '__main__':
    
    afni.base.AFNIBaseCommand.set_default_output_type("NIFTI")
    
    wf = pe.Workflow(name="calculating_measures")
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
    
    epi_mask = pe.Node(interface=afni.Automask(), name="epi_mask")
    wf.connect(datasource, "EPI_bandpassed", epi_mask, "in_file")
    wf.connect(epi_mask, 'out_file', ds, "functional_mask")
    
    reho = create_reho()
    reho.inputs.inputspec.cluster_size = 27
    reho.inputs.inputspec.rest_mask = "/scr/kalifornien1/mindwandering/workingdir/group_analysis/restrict_to_grey/group_mask_masked.nii.gz"
    #wf.connect(epi_mask, "out_file", reho, "inputspec.rest_mask")
    #reho.inputs.inputspec.rest_mask = "/SCR/MNI152_T1_2mm_ones.nii.gz"
    wf.connect(datasource, "EPI_bandpassed", reho, "inputspec.rest_res_filt")
    wf.connect(reho, 'outputspec.z_score', ds, "reho_z")
    
    alff = create_alff()
    alff.inputs.hp_input.hp = 0.01
    alff.inputs.lp_input.lp = 0.1
    alff.inputs.inputspec.rest_mask = "/scr/kalifornien1/mindwandering/workingdir/group_analysis/restrict_to_grey/group_mask_masked.nii.gz"
    #wf.connect(epi_mask, "out_file", alff, "inputspec.rest_mask")
    #reho.inputs.inputspec.rest_mask = "/SCR/MNI152_T1_2mm_ones.nii.gz"
    wf.connect(datasource, "EPI_full_spectrum", alff, "inputspec.rest_res")
    wf.connect(alff, 'outputspec.alff_Z_img', ds, "alff_z")
    wf.connect(alff, 'outputspec.falff_Z_img', ds, "falff_z")
    
    roi_infosource = pe.Node(util.IdentityInterface(fields=["roi"]), name="roi_infosource")
    roi_infosource.iterables = ('roi', rois)
    
    point = pe.Node(afni.Calc(), name="point")
    point.inputs.in_file_a = fsl.Info.standard_image("MNI152_T1_2mm.nii.gz")
    point.inputs.outputtype = "NIFTI"
    point.inputs.out_file = "roi_point.nii"
    def roi2exp(coord):
        return "step(4-(x%+d)*(x%+d)-(y%+d)*(y%+d)-(z%+d)*(z%+d))"%(coord[0], coord[0], coord[1], coord[1], -coord[2], -coord[2])
    wf.connect(roi_infosource, ("roi", roi2exp), point, "expr")
    
    def format_filename(roi_str):
        import string
        valid_chars = "-_.%s%s" % (string.ascii_letters, string.digits)
        return "roi_"+''.join(c for c in str(roi_str).replace(",","_") if c in valid_chars)+"_roi.nii.gz"
    
    sphere = pe.Node(fsl.ImageMaths(), name="sphere")
    sphere.inputs.out_data_type = "float"
    sphere.inputs.op_string = "-kernel sphere 8 -fmean -bin"
    wf.connect(point, "out_file", sphere, "in_file")
    wf.connect(roi_infosource, ("roi", format_filename), sphere, "out_file")
    
    extract_timeseries = pe.Node(afni.Maskave(), name="extract_timeseries")
    extract_timeseries.inputs.quiet = True
    wf.connect(sphere, "out_file", extract_timeseries, "mask")
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
    wf.connect(z_trans, 'out_file', ds, "seed_based_z")
    
    dual_regression_stage1 = get_spatial_map_timeseries()
    dual_regression_stage1.inputs.inputspec.spatial_map = "/scr/adenauer1/PowerFolder/Dropbox/papers/neural_correlates_of_mind_wandering/rsn20.nii.gz"
    dual_regression_stage1.inputs.inputspec.demean = True
    dual_regression_stage1.inputs.inputspec.subject_mask = "/scr/kalifornien1/mindwandering/workingdir/group_analysis/restrict_to_grey/group_mask_masked.nii.gz"
    #wf.connect(epi_mask, "out_file", dual_regression_stage1, "inputspec.subject_mask")
    wf.connect(datasource, "EPI_bandpassed", dual_regression_stage1, "inputspec.subject_rest")
    wf.connect(dual_regression_stage1, "outputspec.subject_timeseries", ds, "dual_regression_timeseries")
     
    dual_regression_stage2 = create_temporal_reg()
    dual_regression_stage2.inputs.inputspec.demean = True
    dual_regression_stage2.inputs.inputspec.normalize = True
    dual_regression_stage2.inputs.inputspec.subject_mask = "/scr/kalifornien1/mindwandering/workingdir/group_analysis/restrict_to_grey/group_mask_masked.nii.gz"
    #wf.connect(epi_mask, "out_file", dual_regression_stage2, "inputspec.subject_mask")
    wf.connect(datasource, "EPI_bandpassed", dual_regression_stage2, "inputspec.subject_rest")
    wf.connect(dual_regression_stage1, "outputspec.subject_timeseries", dual_regression_stage2, "inputspec.subject_timeseries")
    wf.connect(dual_regression_stage2, 'outputspec.temp_reg_map_z_stack', ds, "dual_regression_z")

    downsample_mask = pe.Node(fsl.FLIRT(), name="downsample_mask")
    downsample_mask.inputs.apply_isoxfm = 3
    downsample_mask.inputs.reference = "/scr/adenauer1/3mm_brain.nii.gz"
    downsample_mask.inputs.in_file = "/scr/kalifornien1/mindwandering/workingdir/group_analysis/restrict_to_grey/group_mask_masked.nii.gz"
    downsample_mask.inputs.interp = "nearestneighbour"
    
    downsample_epi = pe.Node(fsl.FLIRT(), name="downsample_epi")
    downsample_epi.inputs.apply_isoxfm = 3
    downsample_epi.inputs.reference = "/scr/adenauer1/3mm_brain.nii.gz"
    wf.connect(datasource, "EPI_bandpassed", downsample_epi, "in_file")
    
    centrality = pe.Node(DegreeCentrality(), name="degree_centrality")
    centrality.plugin_args={'submit_specs': 'request_memory = 20000'}
    centrality.inputs.sparsity_thr = 0.05
    wf.connect(downsample_epi, "out_file", centrality, "epi_file")
    wf.connect(downsample_mask, "out_file", centrality, "mask_file")
     
    z_score_centrality = get_zscore("z_score_centrality")
    wf.connect(centrality, 'dc_map', z_score_centrality, "inputspec.input_file")
    wf.connect(downsample_mask, "out_file", z_score_centrality, "inputspec.mask_file")
    wf.connect(z_score_centrality, 'outputspec.z_score_img', ds, "degree_centrality")

    wf.run(plugin="Linear")


