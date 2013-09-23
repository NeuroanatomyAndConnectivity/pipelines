import nibabel as nb
import numpy as np
import os
from similarity import Similarity
from variables import workingdir, freesurferdir
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
import nipype.interfaces.afni as afni
import subprocess

subject_id = '9630905'
workingdir = '/scr/kongo1/NKIMASKS'

preprocessedfile = '/SCR/Data/results/preprocessed_resting/_session_session1/_subject_id_9630905/_fwhm_0/_bandpass_filter0/afni_corr_rest_roi_dtype_tshift_detrended_regfilt_gms_filt.nii.gz'
regfile = '/SCR/Data/results/func2anat_transform/_session_session1/_subject_id_9630905/_register0/FREESURFER.mat'
parcfile = '/SCR/Data/freesurfer/9630905/mri/aparc.a2009s+aseg.mgz'

def get_mask(labels):
    parcdata = nb.load(parcfile).get_data()
    if labels == []:
        mask = np.ones_like(parcdata)
    else:
        mask = np.zeros_like(parcdata)
        for label in labels:
            newdata = parcdata == label
            mask = mask + newdata
    return mask

#define source mask (surface, volume)
sourcelabels = [12114, 12113] #ctx_rh_G_front_inf-Triangul, ctx_rh_G_front_inf-Orbital
sourcemask = get_mask(sourcelabels)
sourcemaskfile = os.path.join(workingdir,'masks/','sourcemask.nii')
sourceImg = nb.Nifti1Image(sourcemask, None)
nb.save(sourceImg, sourcemaskfile)

#define target mask (surface, volume)
targetlabels = [11114] #ctx_lh_G_front_inf-Triangul
targetmask = get_mask(sourcelabels)
targetmaskfile = os.path.join(workingdir, 'masks/', 'targetmask.nii')
targetImg = nb.Nifti1Image(targetmask, None)
nb.save(targetImg, targetmaskfile)

#invert transform matrix
invt = fsl.ConvertXFM()
invt.inputs.in_file = regfile
invt.inputs.invert_xfm = True
invt.inputs.out_file = regfile + '_inv.mat'
invt_result= invt.run()

#transform anatomical mask to functional space
sourcexfm = fsl.ApplyXfm()
sourcexfm.inputs.in_file = sourcemaskfile
sourcexfm.inputs.in_matrix_file = invt_result.outputs.out_file
sourcexfm.inputs.out_file = sourcemaskfile + '_xfm.nii.gz'
sourcexfm.inputs.reference = preprocessedfile
sourcexfm.inputs.interp = 'nearestneighbour'
sourcexfm.inputs.apply_xfm = True
sourcexfm_result = sourcexfm.run()

#same transform for target
targetxfm = fsl.ApplyXfm()
targetxfm.inputs.in_file = targetmaskfile
targetxfm.inputs.in_matrix_file = invt_result.outputs.out_file
targetxfm.inputs.out_file = targetmaskfile + '_xfm.nii.gz'
targetxfm.inputs.reference = preprocessedfile
targetxfm.inputs.interp = 'nearestneighbour'
targetxfm.inputs.apply_xfm = True
targetxfm_result = targetxfm.run()

sourcemask_xfm = nb.load(sourcexfm_result.outputs.out_file).get_data()
inputdata = nb.load(preprocessedfile).get_data()
#manual source data creation (-mask_source option not yet available in afni)
maskedinput = np.zeros_like(inputdata)
for timepoint in range(inputdata.shape[3]):
    maskedinput[:,:,:,timepoint] = np.where(sourcemask_xfm,inputdata[:,:,:,timepoint],0)
maskedinputfile = os.path.join(workingdir,'masks/','inputfile.nii')
inputImg = nb.Nifti1Image(maskedinput, None)
nb.save(inputImg, maskedinputfile)

#run Similarity
corr = afni.AutoTcorrelate()
corr.inputs.in_file = maskedinputfile
corr.inputs.mask = targetxfm_result.outputs.out_file
corr.inputs.mask_only_targets = True
corr.inputs.out_file = os.path.join(workingdir,'masks/','corr_out.1D')
corr_result = corr.run()

#convert from AFNI file to NIFTI
convert = afni.AFNItoNIFTI()
convert.inputs.in_file = corr_result.outputs.out_file
convert.inputs.out_file = corr_result.outputs.out_file + '.nii'
convert_result = convert.run()
