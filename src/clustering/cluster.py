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
from variables import lhvertices, rhvertices, workingdir
import pickle

class ClusterInputSpec(BaseInterfaceInputSpec):
    volume = File(exists=True, desc='surface to be clustered', mandatory=True)
    sxfmout = File(exists=True, desc='original surface', mandatory=True)
    hemi = traits.String(exists=True, desc='hemisphere', mandatory=True)
    cluster_type = traits.String(exists=True, desc='spectral, hiercluster, kmeans, or dbscan', mandatory=True)
    n_clusters = traits.Int(exists=True, desc='number of clusters', mandatory=True)

class ClusterOutputSpec(TraitedSpec):
    clustered_volume = File(exists=True, desc="clustered volume")

class Cluster(BaseInterface):
    input_spec = ClusterInputSpec
    output_spec = ClusterOutputSpec

    def _run_interface(self, runtime):        
        fname = self.inputs.volume
        #load data, read lines 8~penultimate
        datafile = open(fname, 'rb')
        data = [i.strip().split() for i in datafile.readlines()]
        stringmatrix = data[8:-1]
        datafile.close()

        if self.inputs.hemi == 'lh': chosenvertices = lhvertices
        if self.inputs.hemi == 'rh': chosenvertices = rhvertices
        corrmatrix = np.zeros((len(chosenvertices),len(chosenvertices)))
        for x, vertex in enumerate(chosenvertices):
        	for i in xrange(len(chosenvertices)):
	            corrmatrix[x][i] = abs(float(stringmatrix[vertex][i]))
        if self.inputs.cluster_type == 'spectral':
            labels = spectral(corrmatrix, n_clusters=self.inputs.n_clusters, mode='arpack')
        if self.inputs.cluster_type == 'hiercluster':
            labels = Ward(n_clusters=self.inputs.n_clusters).fit_predict(corrmatrix)
        if self.inputs.cluster_type == 'kmeans':
            labels = km(n_clusters=self.inputs.n_clusters).fit_predict(corrmatrix)
        if self.inputs.cluster_type == 'dbscan':
            labels = DBSCAN(eps=np.average(corrmatrix)+np.std(corrmatrix)).fit_predict(corrmatrix)
        sxfmout = self.inputs.sxfmout
        img = nb.load(sxfmout)

        outarray = -np.ones(shape=img.shape[0])
        for j, cluster in enumerate(labels):
            outarray[chosenvertices[j]] = cluster+1

        new_img = nb.Nifti1Image(outarray, img.get_affine(), img.get_header())
        _, base, _ = split_filename(fname)
        nb.save(new_img, os.path.abspath(base + '_clustered.nii'))

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        fname = self.inputs.volume
        _, base, _ = split_filename(fname)
        outputs["clustered_volume"] = os.path.abspath(base+'_clustered.nii')
        return outputs
