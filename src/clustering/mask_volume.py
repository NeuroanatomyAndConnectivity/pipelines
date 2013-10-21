import nibabel as nb
import numpy as np
import os

from variables import workingdir
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename

from utils import get_mask

#labels
sourcelabels = [12114, 12113] #ctx_rh_G_front_inf-Triangul, ctx_rh_G_front_inf-Orbital
targetlabels = [11114] #ctx_lh_G_front_inf-Triangul
inputlabels = sourcelabels + targetlabels

class MaskVolumeInputSpec(BaseInterfaceInputSpec):
    preprocessedfile = File(exists=True, desc='original volume', mandatory=True)
    regfile = File(exists=True, desc='register .mat file', mandatory=True)

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
        sourcemask = get_mask(inputlabels)
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
        targetlabels = [11114] #ctx_lh_G_front_inf-Triangul
        targetmask = get_mask(targetlabels)
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

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["volume_input_mask"] = 'inputfile.nii'
        outputs["volume_source_mask"] = 'sourcemask.nii'
        outputs["volume_target_mask"] = 'targetmask.nii'
        return outputs
