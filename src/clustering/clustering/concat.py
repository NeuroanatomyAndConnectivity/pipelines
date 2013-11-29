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
    targetmask = File(exists=True, desc='total target mask')

class Concat(BaseInterface):
    input_spec = ConcatInputSpec
    output_spec = ConcatOutputSpec

    def _run_interface(self, runtime):
        ##load data
        vol = nb.load(self.inputs.volume_input).get_data()
        surf = nb.load(self.inputs.surface_input).get_data()
        vol_target = nb.load(self.inputs.volume_target_mask).get_data()
        surf_mask = nb.load(self.inputs.surface_mask).get_data()

        ##CONCATENATE INPUT##
        volumeinput = np.resize(vol,(vol.size/vol.shape[-1],vol.shape[-1]))
        surfaceinput = np.squeeze(surf)
        totalinput = np.concatenate((surfaceinput,volumeinput))

        ##SQUEEZE SPARSE MATRIX##
        input_sum = np.sum(totalinput,axis=1) #find rows of all zeroes
        the_indices = np.where(input_sum!=0)[0] #save indices for reinflation after squeeze
        np.save(os.path.abspath('indices.npy'),the_indices)
        #squeeze & save
        denseinput = totalinput[the_indices]
        niftishape = np.reshape(denseinput,(-1,1,1,vol.shape[3]))#reshape into proper nifti (N,1,1,time)
        inputfile = os.path.abspath('simInput.nii')
        nImg = nb.Nifti1Image(niftishape, None)
        nb.save(nImg, inputfile)

        ##CONCATENATE TARGET##
        volumetarget = np.reshape(vol_target,(vol_target.size))
        surfacetarget = surf_mask[:,0,0,0] ##one timepoint
        totaltarget = np.concatenate((surfacetarget,volumetarget))
        densetarget = np.array(totaltarget[the_indices],dtype='f') ##squeeze target mask, save as float32 for afni input
        targetfile = os.path.abspath('simTarget.nii')
        nImg = nb.Nifti1Image(densetarget, None)
        nb.save(nImg, targetfile)


##CHANGE TO 3DTCORRMAP???

        #run Connectivity (source x target)
        corr = afni.AutoTcorrelate()  #3dWarp -deoblique ??
        corr.inputs.in_file = inputfile
        corr.inputs.mask = targetfile
        corr.inputs.mask_only_targets = True
        corr.inputs.out_file = os.path.abspath('corr_out.1D')
        corr_result = corr.run()
        #convert from AFNI file to NIFTI & mask to pFC
        convert = afni.AFNItoNIFTI()
        convert.inputs.in_file = corr_result.outputs.out_file
        convert.inputs.out_file = os.path.abspath('connectivity.1D.nii')
        convert_result = convert.run()

        connectivity = nb.load(convert_result.outputs.out_file).get_data()
        mask = nb.load(targetfile).get_data()
        mask_asBool = np.asarray(mask,dtype=np.bool)
        maskedconnectivity = connectivity[mask_asBool,:,:,:]
        nImg = nb.Nifti1Image(maskedconnectivity,None)
        nb.save(nImg, os.path.abspath('similarity.1D.nii'))

        if self.inputs.sim_type!='temp':
            #make Similarity matrix (target x target) for eta2 and spat
            sim = afni.AutoTcorrelate()
            sim.inputs.in_file = os.path.abspath('similarity.1D.nii')
            sim.inputs.out_file = os.path.abspath('similarity.1D')
            sim.inputs.eta2 = self.inputs.sim_type=='eta2' #True for eta2
            sim_result = sim.run()
            #convert from AFNI file to NIFTI
            convert = afni.AFNItoNIFTI()
            convert.inputs.in_file = sim_result.outputs.out_file
            convert.inputs.out_file = os.path.abspath('similarity.1D.nii')
            convert_result = convert.run()

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["simmatrix"] = os.path.abspath('similarity.1D.nii')
        outputs["maskindex"] = os.path.abspath('indices.npy')
        outputs["targetmask"] = os.path.abspath('simTarget.nii')
        return outputs
