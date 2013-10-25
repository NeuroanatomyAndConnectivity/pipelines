import os
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec

import numpy as np
import nibabel as nb
from variables import workingdir, lhvertices, rhvertices, lhsource, rhsource

class MaskSurfaceInputSpec(BaseInterfaceInputSpec):
    sxfmout = File(exists=True, desc='original surface', mandatory=True)
    hemi = traits.String(exists=True, desc='hemisphere', mandatory=True)

class MaskSurfaceOutputSpec(TraitedSpec):
    surface_mask = File(exists=True, desc="surface target as mask")
    surface_data = File(exists=True, desc="surface masked by sourcemask")

class MaskSurface(BaseInterface):
    input_spec = MaskSurfaceInputSpec
    output_spec = MaskSurfaceOutputSpec

    def _run_interface(self, runtime):
        sxfmout = self.inputs.sxfmout
        hemi = self.inputs.hemi

        data = nb.load(sxfmout).get_data()
        origdata = data.shape
        affine = None
        data.resize(data.shape[0]*data.shape[2],1,1,data.shape[3]) #in case of fsaverage, where nifti splits large dim

        sourcemask = np.zeros(origdata, dtype=np.int)
        targetmask = np.zeros(origdata, dtype=np.int)
        if hemi == 'lh': 
            sourcemask[lhsource] = 1
            targetmask[lhvertices] = 1
        if hemi == 'rh': 
            sourcemask[rhsource] = 1
            targetmask[rhvertices] = 1

        targetmask.resize(origdata)
        targetmaskImg = nb.Nifti1Image(targetmask, affine)
        nb.save(targetmaskImg, 'surfacemask.nii')

        ## make new input data with source mask
        sourcedata = np.where(sourcemask,data,0)
        sourcedata.resize(origdata)
        sourcedataImg = nb.Nifti1Image(sourcedata, affine)
        nb.save(sourcedataImg, 'surfacedata.nii')
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["surface_mask"] = 'surfacemask.nii'
        outputs["surface_data"] = 'surfacedata.nii'
        return outputs
