import os
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec

import numpy as np
import nibabel as nb
from clustering.utils import get_vertices

class MaskSurfaceInputSpec(BaseInterfaceInputSpec):
    sxfmout = File(exists=True, desc='original surface', mandatory=True)
    hemi = traits.String(exists=True, desc='hemisphere', mandatory=True)
    fs = traits.String(exists=True, desc='fsaverage', mandatory=True)
    freesurferdir = traits.String(exists=True, desc='freesurfer directory', mandatory=True)
    sourcelabels = traits.ListInt(exists=True, desc= 'source labels', mandatory=True)
    targetlabels = traits.ListInt(exists=True, desc= 'target labels', mandatory=True)

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

        #define which vertices are in the ROI
        source_vertices = get_vertices(self.inputs.hemi, self.inputs.freesurferdir, self.inputs.fs, self.inputs.sourcelabels)
        target_vertices = get_vertices(self.inputs.hemi, self.inputs.freesurferdir, self.inputs.fs, self.inputs.targetlabels)

        #create masks for source and target vertices
        sourcemask[source_vertices] = 1
        targetmask[target_vertices] = 1

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
