import surfer
from surfer import Brain
import numpy as np
import nibabel as nb
import nipype.interfaces.freesurfer as fs
#from variables import freesurferdir, resultsdir
import os
import glob
import sys

def annotation():
	brain.add_annotation('aparc.a2009s', alpha = .2)
def roi():
	brain.add_label('prefrontal', alpha = .4)
def save(filename):
	brain.save_montage(filename+'.png',['med', 'lat', 'ros', 'vent'],orientation = 'h') #to save png
def all_brains(dir):
    for root, dirs, filenames in os.walk(dir):
        for f in filenames:
            hemi = f[:2]
            if hemi == 'De' or hemi == 'te':
                hemi = 'lh'
            if f.endswith('nii'):
                print f, hemi
                clustermap = nb.load(os.path.join(root,f)).get_data()
                add_cluster(clustermap, hemi)
                save(os.path.join(root,f))

def add_cluster(clustermap, hemi, fsaverage):
    brain = Brain(fsaverage, hemi, surface,config_opts=dict(background="lightslategray", cortex="high_contrast"))
    brain.add_data(clustermap, colormap='spectral', alpha=.8)
    brain.data['colorbar'].number_of_colors = int(clustermap.max())+1
    brain.data['colorbar'].number_of_labels = int(clustermap.max())+1 ##because -1 denotes masked regions, cluster labels start at 1

if __name__ == '__main__' :
	#fs.FSCommand.set_default_subjects_dir('SCR/data/Final_High')#(freesurferdir)
	#pysurfer visualization
    fsaverage = 'fsaverage4'
    hemi = 'lh'
    surface = 'pial'
    brain = Brain(fsaverage, hemi, surface, config_opts=dict(background="lightslategray", cortex="high_contrast"))
    print('FORMAT: add_cluster(clustermap,hemisphere,fsaverage)')
