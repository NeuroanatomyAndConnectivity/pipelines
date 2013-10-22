import numpy as np
import nibabel as nb
import os
import nipype.interfaces.afni as afni
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec

class ConcatInputSpec(BaseInterfaceInputSpec):
    volume_input = File(exists=True, desc="input volume for similarity")
    surface_input = File(exists=True, desc="input surface")
    volume_target_mask = File(exists=True, desc="target volume as mask")
    surface_mask = File(exists=True, desc="target surface as mask")
    sim_type = traits.String(exists=True, desc='temp, eta2, or spat', mandatory=True)

class ConcatOutputSpec(TraitedSpec):
    simmatrix = File(exists=True, desc="output similarity")
    maskindex = File(exists=True, desc='index for later returning to anat space')

class Concat(BaseInterface):
    input_spec = ConcatInputSpec
    output_spec = ConcatOutputSpec

    def _run_interface(self, runtime):
        ##CONCATENATE INPUT##
        vol = self.inputs.volume_input
        volumeinput = np.resize(vol,(vo.size/vol.shape[-1],vol.shape[-1]))
        surfaceinput = np.squeeze(self.inputs.surface_input)
        totalinput = np.concatenate((surfaceinput,volumeinput))

        ##SQUEEZE SPARSE MATRIX##
        input_sum = np.sum(totalinput,axis=1) #find rows of all zeroes
        the_indices = np.where(input_sum!=0)[0] #save indices for reinflation after squeeze
        np.save('indices.npy',the_indices)
        #squeeze & save
        denseinput = totalinput[the_indices]
        niftishape = np.reshape(denseinput,(-1,1,1,vol.shape[3]))#reshape into proper nifti (N,1,1,time)
        inputfile = 'simInput.nii'
        nImg = nb.Nifti1Image(niftishape, None)
        nb.save(nImg, inputfile)

        ##CONCATENATE TARGET##
        volumetarget = np.reshape(self.inputs.volume_target_mask,(self.inputs.volume_target_mask.size))
        surfacetarget = self.inputs.surface_mask[:,0,0,0] ##one timepoint
        totaltarget = np.concatenate((surfacetarget,volumetarget))
        densetarget = totaltarget[the_indices] ##squeeze target mask
        targetfile = 'simTarget.nii'
        nImg = nb.Nifti1Image(densetarget, None)
        nb.save(nImg, targetfile)

        #run Connectivity (source x target)
        corr = afni.AutoTcorrelate()  #3dWarp -deoblique ??
        corr.inputs.in_file = inputfile
        corr.inputs.mask = targetfile
        corr.inputs.mask_only_targets = sim_type!='temp' #False for temp, True for eta2 and spat
        corr.inputs.out_file = 'corr_out.1D'
        corr_result = corr.run()

        if self.inputs.sim_type=='temp':
            sim_file = corr_result.outputs.out_file
        else:
            #run Similarity (target x target) for eta2 and spat
            sim = afni.AutoTcorrelate()
            sim.inputs.in_file = corr_result.outputs.out_file
            sim.inputs.out_file = 'similarity.1D'
            sim.inputs.eta2 = self.inputs.sim_type=='eta2' #True for eta2
            sim_result = sim.run()
            sim_file = sim_result.outputs.out_file
        
        #convert from AFNI file to NIFTI
        convert = afni.AFNItoNIFTI()
        convert.inputs.in_file = sim_file
        convert.inputs.out_file = convert.inputs.in_file + '.nii'
        convert_result = convert.run()

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["simmatrix"] = 'similarity.1D.nii'
        outputs["maskindex"] = 'indices.npy'
        return outputs
