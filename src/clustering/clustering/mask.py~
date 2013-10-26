import os
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename

import numpy as np
import nibabel as nb
from variables import workingdir, lhvertices, rhvertices

class MaskInputSpec(BaseInterfaceInputSpec):
    sxfmout = File(exists=True, desc='original surface', mandatory=True)
    hemi = traits.String(exists=True, desc='hemisphere', mandatory=True)

class MaskOutputSpec(TraitedSpec):
    mask_volume = File(exists=True, desc="mask volume")

class Mask(BaseInterface):
    input_spec = MaskInputSpec
    output_spec = MaskOutputSpec

    def _run_interface(self, runtime):
        sxfmout = self.inputs.sxfmout
        hemi = self.inputs.hemi
        _, base, _ = split_filename(sxfmout)

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
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        fname = self.inputs.sxfmout
        _, base, _ = split_filename(fname)
        outputs["mask_volume"] = os.path.abspath(base+'_mask.nii')
        return outputs
