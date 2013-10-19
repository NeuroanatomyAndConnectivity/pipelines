import numpy as np
import nibabel as nb
import os
import nipype.interfaces.afni as afni

workingdir = '/scr/kongo1/NKIMASKS'

sxfm = nb.load('/scr/schweiz1/Data/results/sxfmout/_session_session1/_subject_id_9630905/_fwhm_0/_hemi_lh/lh.afni_corr_rest_roi_dtype_tshift_detrended_regfilt_gms_filt.fsaverage4.nii').get_data()
maskedinput = nb.load('/scr/kongo1/NKIMASKS/masks/inputfile.nii').get_data()
sourcemask = nb.load('/scr/kongo1/NKIMASKS/masks/sourcemask.nii_xfm.nii.gz').get_data()
targetmask = nb.load('/scr/kongo1/NKIMASKS/masks/targetmask.nii_xfm.nii.gz').get_data()
surfacemask = nb.load('/scr/schweiz1/Data/cluster_analysis/main_workflow/_hemi_lh/_session_session1/_subject_id_9630905/mask/lh.afni_corr_rest_roi_dtype_tshift_detrended_regfilt_gms_filt.fsaverage4_mask.nii').get_data()

##CONCATENATE INPUT##
volumeinput = volumeinput = np.resize(maskedinput,(maskedinput.size/maskedinput.shape[-1],maskedinput.shape[-1]))
surfaceinput = np.squeeze(sxfm)
totalinput = np.concatenate((surfaceinput,volumeinput))

##SQUEEZE SPARSE MATRIX##
input_sum = np.sum(totalinput,axis=1) #find rows of all zeroes
the_indices = np.where(input_sum!=0)[0] #save indices for reinflation after squeeze
np.save(os.path.join(workingdir, 'indices.npy'),the_indices)
#squeeze & save
denseinput = totalinput[the_indices]
niftishape = np.reshape(denseinput,(-1,1,1,maskedinput.shape[3]))#reshape into proper nifti (N,1,1,time)
inputfile = os.path.join(workingdir, 'simInput.nii')
nImg = nb.Nifti1Image(niftishape, None)
nb.save(nImg, inputfile)

##CONCATENATE TARGET##
volumetarget = np.reshape(targetmask,(targetmask.size))
surfacetarget = surfacemask[:,0,0,0] ##one timepoint
totaltarget = np.concatenate((surfacetarget,volumetarget))
densetarget = totaltarget[the_indices] ##squeeze target mask
targetfile = os.path.join(workingdir, 'simTarget.nii')
nImg = nb.Nifti1Image(densetarget, None)
nb.save(nImg, targetfile)

#run Connectivity (source x target)
corr = afni.AutoTcorrelate()  #3dWarp -deoblique ??
corr.inputs.in_file = inputfile
corr.inputs.mask = targetfile
corr.inputs.mask_only_targets = True
corr.inputs.out_file = os.path.join(workingdir,'masks/corr_out.1D')
corr_result = corr.run()

#run Similarity (target x target)
sim = afni.AutoTcorrelate()
sim.inputs.in_file = corr_result.outputs.out_file
sim.inputs.out_file = os.path.join(workingdir,'masks/sim_out.1D')
sim_result = sim.run()

#convert from AFNI file to NIFTI
convert = afni.AFNItoNIFTI()
convert.inputs.in_file = sim_result.outputs.out_file
convert.inputs.out_file = sim_result.outputs.out_file + '.nii'
convert_result = convert.run()
