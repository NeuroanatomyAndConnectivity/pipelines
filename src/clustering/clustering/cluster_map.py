import nibabel as nb
import numpy as np
import os
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename

class ClusterMapInputSpec(BaseInterfaceInputSpec):
    clusteredfile = File(exists=True, desc='clustered data', mandatory=True)
    indicesfile = File(exists=True, desc='indices .npy file from before similarity', mandatory=True)
    maskfile = File(exists=True, desc='total target mask', mandatory=True)

class ClusterMapOutputSpec(TraitedSpec):
    clustermapfile = File(exists=True, desc="clustered data with proper indices in nifti")
    clustermaptext = File(exists=True, desc="clustered data with proper indices as text")


class ClusterMap(BaseInterface):
    input_spec = ClusterMapInputSpec
    output_spec = ClusterMapOutputSpec

    def _run_interface(self, runtime):
        data = nb.load(self.inputs.clusteredfile).get_data() #clustered data
        mask = nb.load(self.inputs.maskfile).get_data() #target mask
        indices = np.load(self.inputs.indicesfile) #indices of non-zero values used as input for similarity

        mask_bool = np.asarray(mask,dtype=np.bool) #change mask to boolean values
        expandedmask = np.zeros((indices.max()+1),dtype=np.bool) #inititalize mask to incorporate zero-value indices
        expandedmask[indices] = mask_bool
        clustermap = np.zeros_like(expandedmask,dtype=np.float) #back to correct indices values for surface data.
        clustermap[expandedmask] = data
        new_img = nb.Nifti1Image(clustermap, None)
        _, base, _ = split_filename(self.inputs.clusteredfile)
        np.savetxt(os.path.abspath(base+'_clustermap.txt'), np.reshape(clustermap, (1, clustermap.size)), fmt='%d',delimiter=' ')
        nb.save(new_img, os.path.abspath(base+'_clustermap.nii'))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        fname = self.inputs.clusteredfile
        _, base, _ = split_filename(fname)
        outputs["clustermapfile"] = os.path.abspath(base+'_clustermap.nii')
        outputs["clustermaptext"] = os.path.abspath(base+'_clustermap.txt')
        return outputs
