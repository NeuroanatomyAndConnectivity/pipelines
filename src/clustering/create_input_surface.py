import nibabel as nb

sxfm = nb.load('/scr/schweiz1/Data/results/sxfmout/_session_session1/_subject_id_9630905/_fwhm_0/_hemi_lh/lh.afni_corr_rest_roi_dtype_tshift_detrended_regfilt_gms_filt.fsaverage4.nii').get_data()

##from mask_surface import MaskSurface
data = nb.load(sxfmout).get_data()
origdata = data.shape
affine = nb.spatialimages.SpatialImage.get_affine(nb.load(sxfmout))
data.resize(data.shape[0]*data.shape[2],1,1,data.shape[3])
mask = np.zeros_like(data)
if hemi == 'lh': chosenvertices = lhvertices
if hemi == 'rh': chosenvertices = rhvertices
for i,vertex in enumerate(chosenvertices):
    mask[vertex][:] = 1
mask.resize(origdata)
maskImg = nb.Nifti1Image(mask, affine)

nb.save(maskImg, os.path.abspath(base + '_mask.nii'))


