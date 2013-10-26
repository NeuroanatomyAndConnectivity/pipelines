import os

workingdir = os.path.abspath("/scr/ilz1/Data/")
preprocdir = os.path.abspath('/scr/ilz1/Data/preprocResults/')
clusterdir = os.path.abspath('/scr/ilz1/Data/clusterResults/')
interclusterdir = os.path.abspath('/scr/ilz1/Data/consensusResults/')
freesurferdir = os.path.abspath('/scr/ilz1/Data/freesurfer/')
dicomdir = os.path.abspath('/scr/ilz1/Data/DICOM/')

from utils import get_vertices, get_subjects_from

#Subjects & Sessions#
subjects = ['3795193']
#, '3201815', '0021024', '3893245', '3315657', '1961098', '7055197', '2842950', '2475376', '1427581', '4288245', '3808535', '0021001', '8735778', '9630905', '0021018', '3313349', '0021006', '0021002', '1793622', '2799329', '8574662', '4176156']
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
surface_targetlabels = [1, 5, 13, 14, 15, 16, 24, 31, 32, 39, 40, 53, 54, 55, 63, 64, 65, 71]
lhsource = get_vertices('lh',freesurferdir, surface_sourcelabels)
rhsource = get_vertices('rh',freesurferdir, surface_sourcelabels)
lhvertices = get_vertices('lh',freesurferdir, surface_targetlabels)
rhvertices = get_vertices('rh',freesurferdir, surface_targetlabels)

#Analysis Parameters#
hemispheres = ['lh', 'rh']
similarity_types = ['eta2', 'spat', 'temp']
cluster_types = ['hiercluster']#, 'kmeans', 'spectral', 'dbscan']
intercluster_input = ['spectral', 'hiercluster', 'kmeans']#remove dbscan for now
n_clusters = [8]#[02,03,04,05,06,07,10,11,12,13,14,15,16,17,18,19,20,21,22]
epsilon = [.03]
