from nipype.interfaces import afni as afni
import os
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename

class SimilarityInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, desc='surface data to construct similarity matrix', mandatory=True)
    sim = traits.String(exists=True, desc='type of similarity', mandatory=True)
    mask = File(exists=True, desc='mask surface which is correlation target', mandatory=True)

class SimilarityOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="similarity matrix output")
    
class Similarity(BaseInterface):
    input_spec = SimilarityInputSpec
    output_spec = SimilarityOutputSpec

    def _run_interface(self, runtime):
        ##correlationmatrix##
        corr = afni.AutoTcorrelate()
        corr.inputs.in_file = self.inputs.in_file
        corr.inputs.mask= self.inputs.mask
        corr.inputs.mask_only_targets = self.inputs.sim!='temp'
        corr.inputs.out_file = os.path.abspath(self.inputs.sim+'_simmatrix.1D')

        ##pipe output through another correlation, unless sim type is temp##
        corr_res = corr.run()

        if self.inputs.sim!='temp':    
            ##similaritymatrix##
            similarity = afni.AutoTcorrelate()
            similarity.inputs.polort = -1
            similarity.inputs.eta2 = self.inputs.sim=='eta2'
            similarity.inputs.in_file = corr.inputs.out_file
            similarity.inputs.out_file = os.path.abspath(self.inputs.sim+'_simmatrix.1D')
            sim_res = similarity.run()

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = os.path.abspath(self.inputs.sim+'_simmatrix.1D')
        return outputs
