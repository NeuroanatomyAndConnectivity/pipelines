import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs

from CPAC.registration.registration import create_nonlinear_register

from resting_state_preprocessing import subjects

def create_normalization_wf(transformations=["mni2func"]):
    wf = pe.Workflow(name="normalization")
    inputspec = pe.Node(util.IdentityInterface(fields=['T1','skullstripped_T1', 
                                                       'preprocessed_epi', 
                                                       'func2anat_transform']), 
                        name="inputspec")
    
    anat2mni = create_nonlinear_register("anat2mni")
    
    skull_mgz2nii = pe.Node(fs.MRIConvert(out_type="nii"), name="skull_mgs2nii")
    skull_mgz2nii.inputs.slice_reverse=True #othervise the volumes were upside-down!
    skull_mgz2nii.inputs.out_orientation='RAS' #improved FSL interoperability
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
        mni_warp.inputs.ref_file = fsl.Info.standard_image("MNI152_T1_1mm.nii.gz")
        wf.connect(inputspec, 'preprocessed_epi', mni_warp, 'in_file')
        wf.connect(anat2mni, 'outputspec.nonlinear_xfm', mni_warp, 'field_file')
        wf.connect(inputspec, 'func2anat_transform', mni_warp, 'premat')
        
    return wf

if __name__ == '__main__':
    
    #subjects = ["14102.d1"]
    
    
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = "/Users/filo/workdir/rs_analysis/"
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
    
    subject_id_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_id_infosource")
    subject_id_infosource.iterables = ("subject_id", subjects)
    
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=['preprocessed_epi','func2anat_transform']), name="datagrabber")
    datagrabber.inputs.base_directory = '/Users/filo/results/volumes/'
    datagrabber.inputs.template = '%s/_subject_id_%s/%s*/*.%s'
    datagrabber.inputs.template_args['preprocessed_epi'] = [['preprocessed_resting', 'subject_id', '_fwhm_5/', 'nii.gz']]
    datagrabber.inputs.template_args['func2anat_transform'] = [['func2anat_transform','subject_id', '', 'mat']]
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
    
    ds = pe.Node(nio.DataSink(), name="datasink")
    results_dir = '/Users/filo/results'
    ds.inputs.base_directory = results_dir + "/volumes"
    wf.connect(normalize, 'anat2mni.outputspec.output_brain', ds, "normalized_T1")
    wf.connect(normalize, 'anat2mni.outputspec.nonlinear_xfm', ds, "anat2mni_transform")
    wf.connect(normalize, 'invert_warp.inverted_warp_file', ds, "mni2anat_transform")

    wf.run(plugin="MultiProc", plugin_args={'n_procs':6})