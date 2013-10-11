from nipype.interfaces.freesurfer import Surface2VolTransform
from neurosynth.base.dataset import Dataset
from neurosynth.analysis import meta
import nibabel as nb
import numpy as np
import cPickle
import os

## convert niftis by reshaping to add extra dimensions
def to3dNifti(file_1d):
    matrix_1d = nb.load(file_1d).get_data()
    matrix_3d = np.reshape(matrix_1d,(matrix_1d.shape[0],1,1,1))
    file_3d = os.path.abspath(file_1d+'_reshaped.nii')
    nImg = nb.Nifti1Image(matrix_3d, None)
    nb.save(nImg, file_3d)
    return file_3d

in_file = '/scr/schweiz1/Data/results/consensus_intersubject/_cluster_hiercluster/_hemi_lh/_n_clusters_7/_session_session1/_sim_temp/temp_17_hiercluster_lh_ConsensusMat_7_hiercluster_lh.nii'

file_3d = to3dNifti(in_file)
volume_file = file_3d + '_volume.nii'
template = '/scr/ilz1/Data/freesurfer/fsaverage4/mri/orig.mgz'
## then transform the clustered surface into volumes 

xfm2vol = Surface2VolTransform()
xfm2vol.inputs.source_file = file_3d
xfm2vol.inputs.identity = 'fsaverage4'
xfm2vol.inputs.hemi = 'lh'
xfm2vol.inputs.transformed_file = volume_file
xfm2vol.inputs.template_file = template
xfm2vol.run()

#make masks to input into neurosynth
def cluster2masks(clusterfile):
    clustermap = nb.load(clusterfile).get_data()
    for x in range(1,clustermap.max()+1):
        clustermask = (clustermap==x).astype(int)
        nImg = nb.Nifti1Image(clustermask, None)
        nb.save(nImg, os.path.abspath(clusterfile+'_clustermask'+str(x)+'.nii'))

cluster2masks(volume_file)

dataset_file = '/home/raid3/watanabe/neurosynth/data/dataset.pkl'
if not os.path.exists(dataset_file):
    dataset = Dataset('/home/raid3/watanabe/neurosynth/data/database.txt')
    dataset.add_features('/home/raid3/watanabe/neurosynth/data/features.txt')
else:
    dataset = cPickle.load(open(dataset_file,'rb'))

clustermask = volume_file+'_clustermask'+str(3)+'.nii'

ids = dataset.get_ids_by_mask(clustermask)
features = dataset.feature_table.get_features_by_ids(ids)

#mri_surf2vol --identity fsaverage4 --surfval /scr/ilz1/Data/attemptsurface.nii --hemi 'lh' --o /scr/ilz1/Data/results/surf2volume.nii --template /scr/ilz1/Data/freesurfer/fsaverage4/mri/orig.mgz
