import os

basedir = os.path.abspath('/scr/ilz1/nki_enhanced/')
workingdir = os.path.join(basedir,'workingdir')

preprocdir = os.path.join(basedir,'Results/preprocResults')
clusterdir = os.path.join(basedir,'Results/clusterResults')
interclusterdir = os.path.join(basedir,'Results/consensusResults')

freesurferdir = os.path.join(basedir,'freesurfer')
niftidir = os.path.join(basedir,'RawData/niftis')
dicomdir = os.path.join(basedir,'RawData/dicoms')


from clustering.utils import get_vertices, get_subjects_from

#Subjects & Sessions#
subjects = ['0186697']
exclude_subjects = ['0021001']
subjects = list(set(subjects) - set(exclude_subjects))

sessions = ['session1','session2']

#slicetime_file = '/scr/schweiz1/data/NKI_High/scripts/sliceTime2.txt'
#rois = [(26,58,0), (-26,58,0), (14,66,0), (-14,66,0), (6,58,0), (-6,58,0)]

#Volume Data
volume_sourcelabels = [12114, 12113] #ctx_rh_G_front_inf-Triangul, ctx_rh_G_front_inf-Orbital
volume_targetlabels = [11114] #ctx_lh_G_front_inf-Triangul

#Surface Data#
surface_sourcelabels = [] #all
surface_targetlabels = [1, 5, 13, 14, 15, 16, 24, 31, 32, 39, 40, 53, 54, 55, 63, 64, 65, 71] #preFrontal Cortex
lhsource = get_vertices('lh', freesurferdir, surface_sourcelabels)
rhsource = get_vertices('rh', freesurferdir, surface_sourcelabels)
lhvertices = get_vertices('lh', freesurferdir, surface_targetlabels)
rhvertices = get_vertices('rh',  freesurferdir, surface_targetlabels)

#Analysis Parameters#
hemispheres = ['lh', 'rh']
similarity_types = ['eta2', 'spat', 'temp']
cluster_types = ['hiercluster', 'kmeans'] #'spectral', 'dbscan']
intercluster_input = ['hiercluster', 'kmeans']
n_clusters = [2,3,4,5,6,7,8,10,11,12,13,14,15,16,17,18,19,20,21,22]
epsilon = .03
