import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.afni as afni

from CPAC.registration.registration import create_nonlinear_register

from resting_state_preprocessing import subjects

def create_normalization_wf(transformations=["mni2func"]):
    wf = pe.Workflow(name="normalization")
    inputspec = pe.Node(util.IdentityInterface(fields=['T1','skullstripped_T1', 
                                                       'preprocessed_epi', 
                                                       'func2anat_transform']), 
                        name="inputspec")
    
    anat2mni = create_nonlinear_register("anat2mni")
    linear_reg = anat2mni.get_node("linear_reg_0")
    linear_reg.inputs.searchr_x = [-180,180]
    linear_reg.inputs.searchr_y = [-180,180]
    linear_reg.inputs.searchr_z = [-180,180]
    
    skull_mgz2nii = pe.Node(fs.MRIConvert(out_type="nii"), name="skull_mgs2nii")
    brain_mgz2nii = skull_mgz2nii.clone(name="brain_mgs2nii")
    wf.connect(inputspec, "skullstripped_T1", brain_mgz2nii, "in_file")
    wf.connect(inputspec, "T1", skull_mgz2nii, "in_file")
    
    anat2mni.inputs.inputspec.reference_skull = fsl.Info.standard_image("MNI152_T1_2mm.nii.gz")
    anat2mni.inputs.inputspec.reference_brain = fsl.Info.standard_image("MNI152_T1_2mm_brain.nii.gz")
    anat2mni.inputs.inputspec.fnirt_config = "T1_2_MNI152_2mm"
    wf.connect(skull_mgz2nii, "out_file", anat2mni, "inputspec.input_skull")
    wf.connect(brain_mgz2nii, "out_file", anat2mni, "inputspec.input_brain")
    
    if 'mni2func' in transformations:
        invert_warp = pe.Node(fsl.InvWarp(), name="invert_warp")
        wf.connect(anat2mni, "outputspec.nonlinear_xfm", invert_warp, "warp_file")
        wf.connect(skull_mgz2nii, "out_file", invert_warp, "ref_file")
    
    if 'func2mni' in transformations:
        mni_warp = pe.Node(interface=fsl.ApplyWarp(),
                       name='mni_warp')
        mni_warp.inputs.ref_file = fsl.Info.standard_image("MNI152_T1_2mm.nii.gz")
        wf.connect(inputspec, 'preprocessed_epi', mni_warp, 'in_file')
        wf.connect(anat2mni, 'outputspec.nonlinear_xfm', mni_warp, 'field_file')
        wf.connect(inputspec, 'func2anat_transform', mni_warp, 'premat')
        
    return wf

if __name__ == '__main__':
    
    #subjects = ["12184.55", "19417.87"]
    
    
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = "/Users/filo/workdir/rs_analysis_test/"
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
    
    subject_id_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_id_infosource")
    subject_id_infosource.iterables = ("subject_id", subjects)
    
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=['epi_mask','preprocessed_epi','func2anat_transform']), name="datagrabber")
    datagrabber.inputs.base_directory = '/Users/filo/results/volumes/'
    datagrabber.inputs.template = '%s/_subject_id_%s/%s*/*.%s'
    datagrabber.inputs.template_args['preprocessed_epi'] = [['preprocessed_resting', 'subject_id', '_fwhm_5/', 'nii.gz']]
    datagrabber.inputs.template_args['func2anat_transform'] = [['func2anat_transform','subject_id', '', 'mat']]
    datagrabber.inputs.template_args['epi_mask'] = [['epi_mask','subject_id', '', 'nii']]
    datagrabber.inputs.sort_filelist = True
    wf.connect(subject_id_infosource, "subject_id", datagrabber, "subject_id")
    
    fs_datagrabber = pe.Node(nio.FreeSurferSource(), name="fs_datagrabber")
    fs_datagrabber.inputs.subjects_dir = '/scr/namibia1/baird/MPI_Project/freesurfer/'
    wf.connect(subject_id_infosource, "subject_id", fs_datagrabber, "subject_id")
    
    normalize = create_normalization_wf()
    wf.connect(datagrabber, "preprocessed_epi", normalize, "inputspec.preprocessed_epi")
    wf.connect(datagrabber, "func2anat_transform", normalize, "inputspec.func2anat_transform")
    wf.connect(fs_datagrabber, "orig", normalize, "inputspec.T1")
    wf.connect(fs_datagrabber, "brain", normalize, "inputspec.skullstripped_T1")
    
    
    inv_func2anat = pe.Node(interface=fsl.utils.ConvertXFM(),
                            name='inv_func2anat')
    inv_func2anat.inputs.invert_xfm = True
    wf.connect(datagrabber, "func2anat_transform", inv_func2anat, "in_file")
    
    roi_infosource = pe.Node(util.IdentityInterface(fields=["roi"]), name="roi_infosource")
    roi_infosource.iterables = ('roi', [(26,58,0), (-26,58,0), (14,66,0), (-14,66,0), (6,58,0), (-6,58,0)])
    
    point = pe.Node(afni.Calc(), name="point")
    point.inputs.in_file_a = fsl.Info.standard_image("MNI152_T1_2mm.nii.gz")
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
    sphere.inputs.op_string = "-kernel sphere 6 -fmean -bin"
    wf.connect(point, "out_file", sphere, "in_file")
    wf.connect(roi_infosource, ("roi", format_filename), sphere, "out_file")
    
    mask2func = pe.Node(fsl.ApplyWarp(), name="mask2func")
    mask2func.inputs.datatype = "float"
    wf.connect(normalize, 'invert_warp.inverted_warp_file', mask2func, "field_file")
    wf.connect(datagrabber, "preprocessed_epi", mask2func, "ref_file")
    wf.connect(sphere, "out_file", mask2func, "in_file")
    wf.connect(inv_func2anat, 'out_file', mask2func, "postmat")
    
    threshold = pe.Node(fs.Binarize(min=0.5, out_type='nii'), name="threshold")
    wf.connect(mask2func, "out_file", threshold, "in_file")
    
    restrict_to_brain = pe.Node(fsl.ApplyMask(), name="restrict_to_brain")
    wf.connect(threshold, "binary_file", restrict_to_brain, "in_file")
    wf.connect(datagrabber, "epi_mask", restrict_to_brain, "mask_file")
    
    extract_timeseries = pe.Node(afni.Maskave(), name="extract_timeseries")
    extract_timeseries.inputs.quiet = True
    wf.connect(restrict_to_brain, "out_file", extract_timeseries, "mask")
    wf.connect(datagrabber, "preprocessed_epi", extract_timeseries, "in_file")
    
    correlation_map = pe.Node(afni.Fim(), name="correlation_map")
    correlation_map.inputs.out = "Correlation"
    correlation_map.inputs.outputtype = "NIFTI_GZ"
    wf.connect(extract_timeseries, "out_file", correlation_map, "ideal_file")
    wf.connect(datagrabber, "preprocessed_epi", correlation_map, "in_file")
    
    z_trans = pe.Node(interface=afni.Calc(), name='z_trans')
    z_trans.inputs.expr = 'log((1+a)/(1-a))/2'
    z_trans.inputs.outputtype = 'NIFTI_GZ'
    wf.connect(correlation_map, "out_file", z_trans, "in_file_a")
    
    def format_filename(roi_str):
        import string
        valid_chars = "-_.%s%s" % (string.ascii_letters, string.digits)
        return "roi_"+''.join(c for c in str(roi_str).replace(",","_") if c in valid_chars)+"_corr_map.nii.gz"
    
    corr2std = pe.Node(fsl.ApplyWarp(), name="corr2std")
    corr2std.inputs.ref_file = fsl.Info.standard_image("MNI152_T1_2mm.nii.gz")
    wf.connect(normalize, 'anat2mni.outputspec.nonlinear_xfm', corr2std, "field_file")
    wf.connect(z_trans, "out_file", corr2std, "in_file")
    wf.connect(datagrabber, "func2anat_transform", corr2std, "premat")
    wf.connect(roi_infosource, ("roi", format_filename), corr2std, "out_file")
    
    ds = pe.Node(nio.DataSink(), name="datasink")
    results_dir = '/Users/filo/results'
    ds.inputs.base_directory = results_dir + "/volumes"
    wf.connect(corr2std, 'out_file', ds, "normalized_z_scored_corr_map")
    wf.connect(normalize, 'anat2mni.outputspec.output_brain', ds, "normalized_T1")
    wf.connect(normalize, 'anat2mni.outputspec.nonlinear_xfm', ds, "anat2mni_transform")
    wf.connect(normalize, 'invert_warp.inverted_warp_file', ds, "mni2anat_transform")

    wf.run(plugin="MultiProc", plugin_args={'n_procs':6})