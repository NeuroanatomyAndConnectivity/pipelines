from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec, InputMultiPath, Directory
from nipype.utils.filemanip import split_filename
import nibabel as nb
import numpy as np
import os
import pickle

class ConsensusInputSpec(BaseInterfaceInputSpec):
    in_Files = traits.Either(InputMultiPath(File(exists=True)),
                                Directory(exists=True),
                                traits.Str(),
                                traits.List(),
                                mandatory=True)

class ConsensusOutputSpec(TraitedSpec):
    out_File = File(exists=True, desc="out_File")
    consensus_mat = File(exists=True, desc='consensus_mat')

class Consensus(BaseInterface):
    input_spec = ConsensusInputSpec
    output_spec = ConsensusOutputSpec

    def _get_filelist(self, trait_input):
        if os.path.isdir(trait_input[0]):
            filelist = []
            for directory in trait_input:
                for root, dirnames, fnames in os.walk(directory):
                    for f in fnames:
                        if f.endswith('.nii'):
                            filelist.append(os.path.join(root,f))
            return filelist
        if os.path.isfile(trait_input[0]): 
            return trait_input

    def makeConsensus(self, eachFile):
        clustermap=nb.load(eachFile).get_data()
        consensus = np.zeros((len(clustermap),len(clustermap)))
        for j in range(len(clustermap)):
            consensus[j] = clustermap == clustermap[j]
        return consensus

    def _run_interface(self, runtime):
        src_paths = self._get_filelist(self.inputs.in_Files)
        sumConsensus = []
        for src_path in src_paths:
            sumConsensus.append(self.makeConsensus(src_path))
        ##average across all consensus instances and output##
        totalConsensus = reduce(lambda x,y: x+y, sumConsensus)/len(sumConsensus)
        pickle.dump(totalConsensus, os.path.abspath(base+'_ConsensusMat')
        ##make consensus into stability measure##
        likeness = abs(totalConsensus-0.5)
        stability = np.mean(likeness,axis=0)
        ##make into NiftiImage##
        nImg = nb.Nifti1Image(stability, None)
        _, base, _ = split_filename(self.inputs.in_Files[0])
        nb.save(nImg, os.path.abspath(base+'_Stability.nii'))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        _, base, _ = split_filename(self.inputs.in_Files[0])
        outputs["out_File"] = os.path.abspath(base+'_Stability.nii')
        outputs['consensus_mat'] = os.path.abspath(base+'_ConsensusMat')
        return outputs
