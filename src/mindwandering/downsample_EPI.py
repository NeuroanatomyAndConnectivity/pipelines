from glob import glob 
import os


for file in glob("*/smri/warped_image/fwhm_6.0/*_wtsimt.nii.gz"):
    if not os.path.exists(file.replace(".nii.gz", "_2mm.nii.gz")):
        os.system("flirt -interp nearestneighbour -in %s -ref %s -applyisoxfm 2 -out %s"%(file, file, file.replace(".nii.gz", "_2mm.nii.gz")))
    #os.remove(file)