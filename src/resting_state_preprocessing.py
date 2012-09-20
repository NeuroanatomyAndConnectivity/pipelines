import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.freesurfer as fs
from bips.workflows.scripts.u0a14c5b5899911e1bca80023dfa375f2.base import create_rest_prep

def create_resting_state_preprocessing_WF(name="preprocess"):
    wf = pe.Workflow(name=name)
    inputspec = pe.Node(util.IdentityInterface(fields=['resting', 'structural']), name="inputspec")
    
    #run Freesurfer
    recon_all = pe.Node(fs.ReconAll(), name="recon_all")
    wf.connect(inputspec, "structural", recon_all, "T1_files")
    
    # generate preprocessing workflow from BIPS
    preproc = create_rest_prep(fieldmap=False)

    # inputs
    preproc.inputs.inputspec.motion_correct_node = 'nipy'
    preproc.inputs.inputspec.realign_parameters = {"loops":[5],
                                                   "speedup":[5]}
    preproc.inputs.inputspec.do_whitening = False
    preproc.inputs.inputspec.timepoints_to_remove = 4
    preproc.inputs.inputspec.smooth_type = 'susan'
    preproc.inputs.inputspec.do_despike = False
    preproc.inputs.inputspec.surface_fwhm = 0.0
    preproc.inputs.inputspec.num_noise_components = 6
    preproc.inputs.inputspec.regress_before_PCA = False
    
    preproc.get_node('fwhm_input').iterables = ('fwhm', [0,5])
    preproc.get_node('take_mean_art').get_node('strict_artifact_detect').inputs.save_plot = False
    preproc.inputs.inputspec.ad_normthresh = 1
    preproc.inputs.inputspec.ad_zthresh = 3
    preproc.inputs.inputspec.tr = 2.3
    preproc.inputs.inputspec.do_slicetime = True
    preproc.inputs.inputspec.sliceorder = range(0,34,2) + range(1,34,2)

    preproc.inputs.inputspec.compcor_select = [True, True]

    preproc.inputs.inputspec.filter_type = 'fsl'
    preproc.inputs.inputspec.highpass_freq = 5
    preproc.inputs.inputspec.lowpass_freq = 128
    preproc.inputs.inputspec.reg_params = [True, True, True, False, True, False]

    wf.connect(recon_all, "subject_id", preproc, 'inputspec.fssubject_id')
    wf.connect(recon_all, "subjects_dir", preproc, 'inputspec.fssubject_dir')
    wf.connect(inputspec, "resting", preproc, "inputspec.func")
    
    return wf

if __name__ == '__main__':
    preprocess = create_resting_state_preprocessing_WF()
    preprocess.base_dir = "/Users/filo/workdir/rs_preprocessing"
    preprocess.crash_dir = "/Users/filo/workdir/rs_preprocessing/crash"
    
    preprocess.inputs.inputspec.resting = "/Users/filo/data/rs_pipeline/GSDT/func/rest.nii"
    preprocess.inputs.inputspec.structural = "/Users/filo/data/rs_pipeline/GSDT/anat/mprage.nii"
    
    preprocess.run(plugin="Linear", plugin_args={"n_procs":4})