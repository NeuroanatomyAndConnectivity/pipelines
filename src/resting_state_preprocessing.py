import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.io as nio
from bips.workflows.scripts.u0a14c5b5899911e1bca80023dfa375f2.base import create_rest_prep
    
if __name__ == '__main__':
    
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = "/Users/filo/workdir/rs_preprocessing"
    
    subject_id_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_id_infosource")
    subject_id_infosource.iterables = ("subject_id", ['02231.e3'])
    
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=['resting_dicoms','resting_nifti','t1_nifti']), name="datagrabber")
    datagrabber.inputs.base_directory = '/scr/namibia1/baird/MPI_Project/Neuroimaging_Data/'
    datagrabber.inputs.template = '%s/%s/%s'
    datagrabber.inputs.template_args['resting_dicoms'] = [['subject_id', '*t2star_epi_2D_resting', '*']]
    datagrabber.inputs.template_args['resting_nifti'] = [['subject_id', 'func', '*.nii.gz']]
    datagrabber.inputs.template_args['t1_nifti'] = [['subject_id', 'anat', '*.nii.gz']]
    datagrabber.inputs.sort_filelist = True
    
    wf.connect(subject_id_infosource, "subject_id", datagrabber, "subject_id")
    
    def get_tr_and_sliceorder(dicom_files):
        import numpy as np
        import dcmstack, dicom
        my_stack = dcmstack.DicomStack()
        for src_path in dicom_files:
            src_dcm = dicom.read_file(src_path)
            my_stack.add_dcm(src_dcm)
        nii_wrp = my_stack.to_nifti_wrapper()
        sliceorder = np.argsort(nii_wrp.meta_ext.get_values('CsaImage.MosaicRefAcqTimes')[0]).tolist()
        tr = nii_wrp.meta_ext.get_values('RepetitionTime')
        return tr/1000.,sliceorder
    
    get_meta = pe.Node(util.Function(input_names=['dicom_files'], output_names=['tr', 'sliceorder'], function=get_tr_and_sliceorder), name="get_meta")
    
    wf.connect(datagrabber, "resting_dicoms", get_meta, "dicom_files")
    
    preproc = create_rest_prep(name="bips_resting_preproc", fieldmap=False)
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
    preproc.inputs.inputspec.do_slicetime = True
    preproc.inputs.inputspec.compcor_select = [True, True]
    preproc.inputs.inputspec.filter_type = 'fsl'
    preproc.inputs.inputspec.highpass_freq = 100
    preproc.inputs.inputspec.lowpass_freq = 10
    preproc.inputs.inputspec.reg_params = [True, True, True, False, True, False]
    preproc.inputs.inputspec.fssubject_dir = '/scr/namibia1/baird/MPI_Project/freesurfer/'
    
    wf.connect(get_meta, "tr", preproc, "inputspec.tr")
    wf.connect(get_meta, "sliceorder", preproc, "inputspec.sliceorder")
    wf.connect(subject_id_infosource, "subject_id", preproc, 'inputspec.fssubject_id')
    wf.connect(datagrabber, "resting_nifti", preproc, "inputspec.func")
    
    wf.run()