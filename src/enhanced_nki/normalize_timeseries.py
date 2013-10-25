import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.afni as afni
import nipype.interfaces.c3 as c3

#from CPAC.registration.registration import create_nonlinear_register

import os
from variables import resultsdir, freesurferdir, subjects, workingdir, rois
from nipype.interfaces import ants

if __name__ == '__main__':
    
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=['func2anat_transform']), name="datagrabber")
    datagrabber.inputs.base_directory = os.path.join(resultsdir,'volumes')
    datagrabber.inputs.template = '%s/_subject_id_%s/%s*/*.%s'
    datagrabber.inputs.template_args['func2anat_transform'] = [['func2anat_transform','subject_id', '', 'mat']]
    datagrabber.inputs.sort_filelist = True
    wf.connect(subject_id_infosource, "subject_id", datagrabber, "subject_id")
    
    timeseries_datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id', 'fwhm'], outfields=['preprocessed_epi']), name="timeseries_datagrabber")
    timeseries_datagrabber.inputs.base_directory = os.path.join(resultsdir,'volumes')
    timeseries_datagrabber.inputs.template = '/preprocessed_resting/_subject_id_%s/_tr_2500/_selector_False.False.False.False.False.False/_fwhm_5/_highpass_freq_-1_lowpass_freq_-1/_bandpass_filter0/*.nii.gz'
    timeseries_datagrabber.inputs.template_args['preprocessed_epi'] = [['subject_id']]
    timeseries_datagrabber.inputs.sort_filelist = True
    wf.connect(subject_id_infosource, "subject_id", timeseries_datagrabber, "subject_id")
    
    func2anat_fsl2itk = pe.Node(c3.C3dAffineTool(), name="func2anat_fsl2itk")
    func2anat_fsl2itk.inputs.itk_transform = True
    func2anat_fsl2itk.inputs.fsl2ras = True
    wf.connect(datagrabber, "func2anat_transform", func2anat_fsl2itk, "transform_file")
    wf.connect(datagrabber, "preprocessed_epi", func2anat_fsl2itk, "source_file")
    wf.connect(ants_normalize, "brain_2nii.out_file", func2anat_fsl2itk, "reference_file")
    
    collect_transforms = pe.Node(
        util.Merge(2),
        name='collect_transforms2')
    wf.connect(func2anat_fsl2itk, "itk_transform", collect_transforms, "in1")
    wf.connect(ants_normalize, "forward_transforms", collect_transforms, "in2")
    
    timeseries2std = pe.Node(ants.WarpTimeSeriesImageMultiTransform(dimension=4), name="timeseries2std")
    timeseries2std.inputs.reference_image = "/usr/share/fsl/data/standard/MNI152_T1_1mm_brain.nii.gz"
    wf.connect(datagrabber, "preprocessed_epi", timeseries2std, "input_image")
    wf.connect(collect_transforms, "out", timeseries2std, "transformation_series")