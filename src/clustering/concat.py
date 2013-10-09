import numpy as np
import nibabel as nb

surface = nb.load('/SCR/Data/results/similarity/_hemi_lh/_session_session1/_subject_id_9630905/_sim_temp/temp.nii').get_data()
volume = nb.load('/scr/kongo1/NKIMASKS/masks/corr_out.1D.nii').get_data()
targetmask = nb.load('/scr/kongo1/NKIMASKS/masks/targetmask.nii_xfm.nii.gz').get_data()

surf = np.squeeze(surface)
vol = np.squeeze(volume)

values = vol[np.where(targetmask)]
linear_vol = np.zeros((vol.shape[0]*vol.shape[1]*vol.shape[2],vol.shape[3]))
cropped_surf = np.zeros((linear_vol.shape[0]))
cropped_surf = surf[:len(cropped_surf)]
