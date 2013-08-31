from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename
import nibabel as nb
import numpy as np
import glob

class ConsensusInputSpec(BaseInterfaceInputSpec):
    in_Files = traits.Either(InputMultiPath(File(exists=True)),
                                Directory(exists=True),
                                traits.Str(),
                                mandatory=True)
    hemi = traits.String(exists=True, desc='hemisphere', mandatory=True)
    cluster_type = traits.String(exists=True, desc='spectral, hiercluster, kmeans, or dbscan', mandatory=True)
    n_clusters = traits.Int(exists=True, desc='number of clusters', mandatory=True)

class ConsensusOutputSpec(TraitedSpec):
    consensus_volume = File(exists=True, desc="consensus volume")

class Consensus(BaseInterface):
    input_spec = ConsensusInputSpec
    output_spec = ConsensusutputSpec

    def _get_filelist(self, trait_input):
        if isinstance(trait_input, str):
            if path.isdir(trait_input):
                return glob(path.join(trait_input, '*.nii'))
            else:
                return glob(trait_input)
        return trait_input

    def makeConsensus(self, eachFile):
        clustermap=nb.load(eachFile).get_data()
        consensus = np.zeros((len(clustermap),len(clustermap)))
        for j in clustermap:
            for i in clustermap:
                consensus[j] = (clustermap[i] == clustermap[j])
        return consensus

    def _run_interface(self, runtime):
        src_paths = self._get_filelist(self.inputs.in_Files)
        sumConsensus = []
        for src_path in src_paths:
            sumConsensus.append(makeConsensus(src_path)

        ##make consensus into probabilities##
        for eachConsensus in sumConsensus
            totalConsensus = reduce(lambda x,y: x+y, sumConsensus)/len(sumConsensus)

        ##make into NiftiImage##
        _, base, _ = split_filename(trait_input)
        #os.makedirs(os.path.dirname(savepath))
        nImg = nb.Nifti1Image(totalConsensus, None)
        nb.save(nImg, os.path.abspath(base + '_clustered.nii'))
