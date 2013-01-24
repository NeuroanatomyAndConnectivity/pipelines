from __future__ import division
import surfer
from surfer import Brain
import os
import numpy as np
import nibabel as nb
import nipype.interfaces.freesurfer as fs
import matplotlib

def annotation():
	brain.add_annotation('aparc.a2009s', alpha = .2)
def roi():
	brain.add_label('prefrontal', alpha = .4)
def save(filename):
	brain.save_montage('/tmp/fsaverage_h_montage'+filename+'.png',['med', 'lat', 'ros', 'vent'],orientation = 'h') #to save png

def get_cluster(hemi,corr,cluster):
	clustermap = nb.load('/SCR/data/11072.b1/results/'+hemi+corr[:4]+'_'+cluster+'.nii').get_data()
	add_cluster(clustermap, hemi)

def add_cluster(clustermap, hemi):
	hemisphere = hemi[-2:]
	brain = Brain(subject_id, hemisphere, surface, config_opts=dict(background="lightslategray", cortex="high_contrast"))
	brain.add_data(clustermap, clustermap.min(), clustermap.max(), colormap='spectral', alpha=.8)
	brain.data["colorbar"].number_of_colors = int(clustermap.max())

if __name__ == '__main__' :
	fs.FSCommand.set_default_subjects_dir('/SCR/data')
	#pysurfer visualization
	subject_id = 'fsaverage4'
	hemi = 'lh'
	surface = 'inflated'
	brain = Brain(subject_id, hemi, surface, config_opts=dict(background="lightslategray", cortex="high_contrast"))

	print('FORMAT: get_cluster(hemi,similarity,cluster)\nCLUSTER TYPES: spectral, kmeans, hiercluster, dbscan')

