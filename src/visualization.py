import surfer
from surfer import Brain
import numpy as np
import nibabel as nb
import nipype.interfaces.freesurfer as fs
from variables import freesurferdir

def annotation():
	brain.add_annotation('aparc.a2009s', alpha = .2)
def roi():
	brain.add_label('prefrontal', alpha = .4)
def save(filename):
	brain.save_montage('/tmp/fsaverage_h_montage'+filename+'.png',['med', 'lat', 'ros', 'vent'],orientation = 'h') #to save png

def add_cluster(clustermap, hemi):
	hemisphere = hemi[-2:]
	brain = Brain(subject_id, hemisphere, surface, config_opts=dict(background="lightslategray", cortex="high_contrast"))
	brain.add_data(clustermap, clustermap.min(), clustermap.max(), colormap='spectral', alpha=.8)
	brain.data["colorbar"].number_of_colors = int(clustermap.max())

if __name__ == '__main__' :
	fs.FSCommand.set_default_subjects_dir(freesurferdir)
	#pysurfer visualization
	subject_id = 'fsaverage4'
	hemi = 'lh'
	surface = 'inflated'
	brain = Brain(subject_id, hemi, surface, config_opts=dict(background="lightslategray", cortex="high_contrast"))

	print('FORMAT: add_cluster(niftifile,hemisphere))

