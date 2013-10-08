from neurosynth.base.dataset import Dataset
from neurosynth.analysis import meta
import cPickle
import os
dataset_file = '/home/raid3/watanabe/neurosynth/data/dataset.pkl'
if not os.path.exists(dataset_file):
    dataset = Dataset('/home/raid3/watanabe/neurosynth/data/database.txt')
    dataset.add_features('/home/raid3/watanabe/neurosynth/data/features.txt')
else:
    dataset = cPickle.load(open(dataset_file,'rb'))
clustermask = '/scr/kongo1/NKIMASKS/masks/targetmask.nii_xfm.nii.gz'

ids = dataset.get_ids_by_mask(clustermask)
features = dataset.feature_table.get_features_by_ids(ids)
