import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import nipype.interfaces.nipy as nipy
from CPAC.reho import create_reho
from CPAC.alff import create_alff
from CPAC.timeseries.timeseries_analysis import get_spatial_map_timeseries
import os
from CPAC.sca.sca import create_temporal_reg


subjects = [
"0102157", 
        "0103645", 
        "0105488", 
        "0106780", 
        "0108355", 
        "0109727", 
        "0111282", 
        "0112249", 
        "0112828", 
        "0113013", 
        "0114232", 
        "0115321", 
        "0115454", 
        "0115564", 
        "0115824", 
        "0116039", 
        "0116065", 
        "0116834", 
        "0116842", 
        "0117168", 
        "0118051", 
        "0119866", 
        "0120557", 
        "0122169", 
        "0122512", 
        "0122816", 
        "0122844", 
        "0123173", 
        "0123429", 
        "0123971", 
        "0125762", 
        "0126919", 
        "0131127", 
        "0131832", 
        "0132717", 
        "0132995", 
        "0134795", 
        "0135671", 
        "0136303", 
        "0136416", 
        "0137073", 
        "0137496", 
        "0137679", 
        "0139300", 
        "0139480", 
        "0141795", 
        "0144667", 
        "0144702", 
        "0146714", 
        "0146865", 
        "0147122", 
        "0150525", 
        "0150589", 
        "0152968", 
        "0153114", 
        "0154423", 
        "0155419", 
        "0155458", 
        "0156263", 
        "0158411", 
        "0158560", 
        "0158744", 
        "0159429", 
        "0161200", 
        "0162251", 
        "0162704", 
        "0162902", 
        "0164900", 
        "0166987", 
        "0167827", 
        "0168239", 
        "0168357", 
        "0168413", 
        "0168489", 
        "0169007", 
        "0173085", 
        "0173286", 
        "0173496", 
        "0174363", 
        "0174886", 
        "0177330", 
        "0177857", 
        "0178174", 
        "0178453", 
        "0179005", 
        "0179873", 
        "0180308", 
        "0182376", 
        "0183457", 
        "0183726", 
        "0185428", 
        "0185676", 
        "0185781", 
        "0186277", 
        "0187635", 
        "0188199", 
        "0188219", 
        "0188854", 
        "0189478", 
        "0190501", 
        "0194023", 
        "0194956", 
        "0195031", 
        "0195236", 
        "0196651", 
        "0197836", 
        "0198051", 
        "0198130", 
        "0198357", 
        "0199340", 
        "0199620"
]

rois = []

# #lMPFC 
rois.append((-6,52,-2))
# #rMPFC 
rois.append((6,52,-2))
# #lPCC 
rois.append((-8,-56,26))
# #rPCC 
rois.append((8,-56,26))

workingdir = "/scr/kalifornien1/mindwandering/workingdir"
resultsdir = "/scr/kalifornien1/mindwandering/results"

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
    wf.connect(epi_mask, "out_file", reho, "inputspec.rest_mask")
    #reho.inputs.inputspec.rest_mask = "/SCR/MNI152_T1_2mm_ones.nii.gz"
    wf.connect(datasource, "EPI_bandpassed", reho, "inputspec.rest_res_filt")
    wf.connect(reho, 'outputspec.z_score', ds, "reho_z")
    
    alff = create_alff()
    alff.inputs.hp_input.hp = 0.01
    alff.inputs.lp_input.lp = 0.1
    wf.connect(epi_mask, "out_file", alff, "inputspec.rest_mask")
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
    wf.connect(epi_mask, "out_file", dual_regression_stage1, "inputspec.subject_mask")
    wf.connect(datasource, "EPI_full_spectrum", dual_regression_stage1, "inputspec.subject_rest")
    
    dual_regression_stage2 = create_temporal_reg()
    dual_regression_stage2.inputs.inputspec.demean = True
    dual_regression_stage2.inputs.inputspec.normalize = True
    wf.connect(epi_mask, "out_file", dual_regression_stage2, "inputspec.subject_mask")
    wf.connect(datasource, "EPI_full_spectrum", dual_regression_stage2, "inputspec.subject_rest")
    wf.connect(dual_regression_stage1, "outputspec.subject_timeseries", dual_regression_stage2, "inputspec.subject_timeseries")
    wf.connect(dual_regression_stage2, 'outputspec.temp_reg_map_z_stack', ds, "dual_regression_z")

    wf.run(plugin="Linear")


