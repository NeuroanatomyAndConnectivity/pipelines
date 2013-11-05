import os
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec

import numpy as np
import nibabel as nb

class MaskSurfaceInputSpec(BaseInterfaceInputSpec):
    sxfmout = File(exists=True, desc='original surface', mandatory=True)
    hemi = traits.String(exists=True, desc='hemisphere', mandatory=True)

class MaskSurfaceOutputSpec(TraitedSpec):
    surface_mask = File(exists=True, desc="surface target as mask")
    surface_data = File(exists=True, desc="surface masked by sourcemask")
    lhvertices = traits.ListInt(exists=True, desc= 'lh target labels', mandatory=True)
    rhvertices = traits.ListInt(exists=True, desc= 'rh target labels', mandatory=True)
    lhsource = traits.ListInt(exists=True, desc= 'lh source labels', mandatory=True)
    rhsource = traits.ListInt(exists=True, desc= 'rh source labels', mandatory=True)

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
            sourcemask[self.inputs.lhsource] = 1
            targetmask[self.inputs.lhvertices] = 1
        if hemi == 'rh': 
            sourcemask[self.inputs.rhsource] = 1
            targetmask[self.inputs.rhvertices] = 1

        targetmask.resize(origdata)
        targetmaskImg = nb.Nifti1Image(targetmask, affine)
        nb.save(targetmaskImg, os.path.abspath('surfacemask.nii'))

        ## make new input data with source mask
        sourcedata = np.where(sourcemask,data,0)
        sourcedata.resize(origdata)
        sourcedataImg = nb.Nifti1Image(sourcedata, affine)
        nb.save(sourcedataImg, os.path.abspath('surfacedata.nii'))

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["surface_mask"] = os.path.abspath('surfacemask.nii')
        outputs["surface_data"] = os.path.abspath('surfacedata.nii')
        return outputs
