import os
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename

from sklearn.cluster import spectral_clustering as spectral
from sklearn.cluster import KMeans as km
from sklearn.cluster import Ward
from sklearn.cluster import DBSCAN
import numpy as np
import nibabel as nb
import os
from variables import lhvertices, rhvertices, workingdir, epsilon

class ClusterInputSpec(BaseInterfaceInputSpec):
    in_File = File(exists=True, desc='surface to be clustered', mandatory=True)
    hemi = traits.String(exists=True, desc='hemisphere', mandatory=True)
    cluster_type = traits.String(exists=True, desc='spectral, hiercluster, kmeans, or dbscan', mandatory=True)
    n_clusters = traits.Int(exists=True, desc='number of clusters', mandatory=True)

class ClusterOutputSpec(TraitedSpec):
    out_File = File(exists=True, desc="clustered volume")

class Cluster(BaseInterface):
    input_spec = ClusterInputSpec
    output_spec = ClusterOutputSpec

    def _run_interface(self, runtime):        
        #load data
        data = nb.load(self.inputs.in_File).get_data()

        if self.inputs.hemi == 'lh': chosenvertices = lhvertices
        if self.inputs.hemi == 'rh': chosenvertices = rhvertices
        corrmatrix = np.zeros((len(chosenvertices),len(chosenvertices)))
        data = np.squeeze(data)

        for x, vertex in enumerate(chosenvertices):
        	for i in xrange(len(chosenvertices)):
        	    if data[vertex][i]>0:
	                corrmatrix[x][i] = data[vertex][i]
        if self.inputs.cluster_type == 'spectral':
            labels = spectral(corrmatrix, n_clusters=self.inputs.n_clusters, mode='arpack')
        if self.inputs.cluster_type == 'hiercluster':
            labels = Ward(n_clusters=self.inputs.n_clusters).fit_predict(corrmatrix)
        if self.inputs.cluster_type == 'kmeans':
            labels = km(n_clusters=self.inputs.n_clusters).fit_predict(corrmatrix)
        if self.inputs.cluster_type == 'dbscan':
            labels = DBSCAN(eps=epsilon).fit_predict(corrmatrix)

        outarray = -np.ones(shape=data.shape[0])
        for j, cluster in enumerate(labels):
            outarray[chosenvertices[j]] = cluster+1

        new_img = nb.Nifti1Image(outarray, None)
        _, base, _ = split_filename(self.inputs.in_File)
        nb.save(new_img, os.path.abspath(base + '_clustered.nii'))

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        fname = self.inputs.in_File
        _, base, _ = split_filename(fname)
        outputs["out_File"] = os.path.abspath(base+'_clustered.nii')
        return outputs
