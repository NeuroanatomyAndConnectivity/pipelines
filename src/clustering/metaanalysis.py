from neurosynth.base.dataset import Dataset
from neurosynth.analysis import meta
from nipype.utils.filemanip import split_filename
import cPickle
import os

from nipype.interfaces.freesurfer import Surface2VolTransform
xfm2vol = Surface2VolTransform()
xfm2vol.inputs.source_file = '/scr/schweiz1/Data/results/compare_subjects/_cluster_kmeans/_hemi_lh/_n_clusters_9/_session_session1/_sim_temp/temp_19_kmeans_lh_Stability.nii'
regfile = '/scr/ilz1/Data/results/func2anat_transform/_session_session1/_subject_id_9630905/_register0/FREESURFER.mat'
xfm2vol.inputs.reg_file = regfile
xfm2vol.inputs.hemi = 'lh'
xfm2vol.inputs.transformed_file = '/scr/ilz1/Data/results/surf2volume.nii'
template = '/scr/ilz1/Data/freesurfer/9630905/mri/orig.mgz'
xfm2vol.inputs.template_file = template
## make dat into mat using maybe convertxfm in FSL
## then transform the clustered surface into volumes, and then make masks to input into neurosynth

def cluster_2_masks(clusterfile):
    _, base, _ = split_filename(clusterfile)
    clustermap = nb.load(clusterfile).get_data()
    for x in range(1,clustermap.max()+1):
        nImg = nb.Nifti1Image(clustermap=x, None)
        nb.save(nImg, os.path.abspath(base+'_Stability.nii'))

dataset_file = '/home/raid3/watanabe/neurosynth/data/dataset.pkl'
if not os.path.exists(dataset_file):
    dataset = Dataset('/home/raid3/watanabe/neurosynth/data/database.txt')
    dataset.add_features('/home/raid3/watanabe/neurosynth/data/features.txt')
else:
    dataset = cPickle.load(open(dataset_file,'rb'))

clustermask = '/scr/kongo1/NKIMASKS/masks/targetmask.nii_xfm.nii.gz'

ids = dataset.get_ids_by_mask(clustermask)
features = dataset.feature_table.get_features_by_ids(ids)

