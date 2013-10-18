import os
import nibabel as nb

workingdir = os.path.abspath("/scr/ilz1/Data/")
resultsdir = os.path.join(workingdir, 'results/')
freesurferdir = os.path.join(workingdir, 'freesurfer/')
dicomdir = os.path.join(workingdir, 'DICOM/')

from utils import get_vertices, get_subjects_from

subjects = ['3795193']
#, '3201815', '0021024', '3893245', '3315657', '1961098', '7055197', '2842950', '2475376', '1427581', '4288245', '3808535', '0021001', '8735778', '9630905', '0021018', '3313349', '0021006', '0021002', '1793622', '2799329', '8574662', '4176156']

exclude_subjects = ['0021001']
subjects = list(set(subjects) - set(exclude_subjects))

analysis_subjects = get_subjects_from(os.path.join(resultsdir,'sxfmout/'))
#['3795193', '3201815', '0021024', '3893245', '1961098', '7055197', '2842950', '2475376', '1427581', '4288245', '3808535', '8735778', '9630905', '0021018','6471972', '3313349', '6471972', '0021006', '0021002', '1793622', '2799329', '8574662', '4176156']

analysis_exclude_subjects = ['3315657','6471972']
analysis_subjects = list(set(analysis_subjects) - set(analysis_exclude_subjects))

sessions = ['session1','session2']
analysis_sessions = ['session1','session2']

#slicetime_file = '/scr/schweiz1/data/NKI_High/scripts/sliceTime2.txt'
#rois = [(26,58,0), (-26,58,0), (14,66,0), (-14,66,0), (6,58,0), (-6,58,0)]

lhvertices = get_vertices('lh',freesurferdir)
rhvertices = get_vertices('rh',freesurferdir)

hemispheres = ['lh', 'rh']
similarity_types = ['eta2', 'spat', 'temp']
cluster_types = ['spectral', 'hiercluster', 'kmeans', 'dbscan']
intercluster_input = ['spectral', 'hiercluster', 'kmeans']#remove dbscan for now
n_clusters = [02,03,04,05,06,07,10,11,12,13,14,15,16,17,18,19,20,21,22]
epsilon = [.03]
