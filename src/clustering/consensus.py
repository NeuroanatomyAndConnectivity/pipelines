from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec, InputMultiPath, Directory
from nipype.utils.filemanip import split_filename
import nibabel as nb
import numpy as np
from glob import glob
import os

class ConsensusInputSpec(BaseInterfaceInputSpec):
    in_Files = traits.Either(InputMultiPath(File(exists=True)),
                                Directory(exists=True),
                                traits.Str(),
                                mandatory=True)

class ConsensusOutputSpec(TraitedSpec):
    out_File = File(exists=True, desc="out_File")

class Consensus(BaseInterface):
    input_spec = ConsensusInputSpec
    output_spec = ConsensusOutputSpec

    def _get_filelist(self, trait_input):
        if isinstance(trait_input, str):
            if os.path.isdir(trait_input):
                filelist = []
                for root, dirnames, fnames in os.walk(trait_input):
                    for f in fnames:
                        if f.endswith('.nii'):
                            filelist.append(os.path.join(root,f))
                return filelist
            else:
                return glob(trait_input)
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
        ##make consensus into stability measure##
        totalConsensus = reduce(lambda x,y: x+y, sumConsensus)/len(sumConsensus)
        likeness = abs(totalConsensus-0.5)
        stability = np.mean(likeness,axis=0)
        ##make into NiftiImage##
        _, base, _ = split_filename(self.inputs.in_Files)
        nImg = nb.Nifti1Image(stability, None)
        nb.save(nImg, os.path.abspath(base + '_consensusStability.nii'))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        _, base, _ = split_filename(self.inputs.in_Files)
        outputs["out_File"] = os.path.abspath(base+'_consensusStability.nii')
        return outputs
