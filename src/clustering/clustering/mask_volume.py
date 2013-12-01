import nibabel as nb
import numpy as np
import os

import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename

from utils import get_mask

class MaskVolumeInputSpec(BaseInterfaceInputSpec):
    preprocessedfile = File(exists=True, desc='original volume', mandatory=True)
    regfile = File(exists=True, desc='register .mat file', mandatory=True)
    parcfile = File(exists=True, desc='parcellation/segmentation file', mandatory=True)
    vol_source = traits.ListInt(exists=True, desc= 'source labels', mandatory=True)
    vol_target = traits.ListInt(exists=True, desc= 'target labels', mandatory=True)

class MaskVolumeOutputSpec(TraitedSpec):
    volume_input_mask = File(exists=True, desc="input volume for similarity")
    volume_source_mask = File(exists=True, desc="source volume as mask")
    volume_target_mask = File(exists=True, desc="target volume as mask")

class MaskVolume(BaseInterface):
    input_spec = MaskVolumeInputSpec
    output_spec = MaskVolumeOutputSpec

    def _run_interface(self, runtime):
        preprocessedfile = self.inputs.preprocessedfile
        regfile = self.inputs.regfile

        #invert transform matrix
        invt = fsl.ConvertXFM()
        invt.inputs.in_file = regfile
        invt.inputs.invert_xfm = True
        invt.inputs.out_file = regfile + '_inv.mat'
        invt_result= invt.run()

        #define source mask (surface, volume)
        input_labels = self.inputs.vol_source+self.inputs.vol_target
        sourcemask = get_mask(input_labels, self.inputs.parcfile)
        sourcemaskfile = os.path.abspath('sourcemask.nii')
        sourceImg = nb.Nifti1Image(sourcemask, None)
        nb.save(sourceImg, sourcemaskfile)

        #transform anatomical mask to functional space
        sourcexfm = fsl.ApplyXfm()
        sourcexfm.inputs.in_file = sourcemaskfile
        sourcexfm.inputs.in_matrix_file = invt_result.outputs.out_file
        _, base, _ = split_filename(sourcemaskfile)
        sourcexfm.inputs.out_file = base + '_xfm.nii.gz'
        sourcexfm.inputs.reference = preprocessedfile
        sourcexfm.inputs.interp = 'nearestneighbour'
        sourcexfm.inputs.apply_xfm = True
        sourcexfm_result = sourcexfm.run()

        #manual source data creation (-mask_source option not yet available in afni)
        sourcemask_xfm = nb.load(sourcexfm_result.outputs.out_file).get_data()
        inputdata = nb.load(preprocessedfile).get_data()
        maskedinput = np.zeros_like(inputdata)
        for timepoint in range(inputdata.shape[3]):
            maskedinput[:,:,:,timepoint] = np.where(sourcemask_xfm,inputdata[:,:,:,timepoint],0)
        maskedinputfile = os.path.abspath('inputfile.nii')
        inputImg = nb.Nifti1Image(maskedinput, None)
        nb.save(inputImg, maskedinputfile)

        ##PREPARE TARGET MASK##

        #define target mask (surface, volume)
        targetmask = get_mask(self.inputs.vol_target, self.inputs.parcfile)
        targetmaskfile = os.path.abspath('targetmask.nii')
        targetImg = nb.Nifti1Image(targetmask, None)
        nb.save(targetImg, targetmaskfile)

        #same transform for target
        targetxfm = fsl.ApplyXfm()
        targetxfm.inputs.in_file = targetmaskfile
        targetxfm.inputs.in_matrix_file = invt_result.outputs.out_file
        _, base, _ = split_filename(targetmaskfile)
        targetxfm.inputs.out_file = base + '_xfm.nii.gz'
        targetxfm.inputs.reference = preprocessedfile
        targetxfm.inputs.interp = 'nearestneighbour'
        targetxfm.inputs.apply_xfm = True
        targetxfm_result = targetxfm.run()

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["volume_input_mask"] = os.path.abspath('inputfile.nii')
        outputs["volume_source_mask"] = os.path.abspath('sourcemask.nii')
        outputs["volume_target_mask"] = os.path.abspath('targetmask.nii')
        return outputs
