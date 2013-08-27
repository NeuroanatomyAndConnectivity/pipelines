import os
import nibabel as nb
subjects = [
            '3795193'#, '3201815', '0021024', '3893245', '3315657', '1961098', '7055197', '2842950', '2475376', '1427581', '4288245', '3808535', '0021001', '8735778', '9630905', '0021018', '3313349', '0021006', '0021002', '1793622', '2799329', '8574662', '4176156',
]

exclude_subjects = ['0021001']
subjects = list(set(subjects) - set(exclude_subjects))

analysis_subjects = ['3795193', '3201815', '0021024', '3893245', '1961098', '7055197', '2842950', '2475376', '1427581', '4288245', '3808535', '8735778', '9630905', '0021018','3315657','6471972', '3313349', '6471972', '0021006', '0021002', '1793622', '2799329', '8574662', '4176156'
]

sessions = ['session1','session2']
analysis_sessions = ['session1','session2']

workingdir = "/SCR/Data/NKI_High"
resultsdir = "/SCR/Data/volumes"
freesurferdir = '/afs/cbs.mpg.de/software/freesurfer/5.1.0/amd64/2.15/subjects'

#slicetime_file = '/scr/schweiz1/data/NKI_High/scripts/sliceTime2.txt'
rois = [(26,58,0), (-26,58,0), (14,66,0), (-14,66,0), (6,58,0), (-6,58,0)]

def getvertices(hemi,freesurferdir):
    labellist = [1, 5, 13, 14, 15, 16, 24, 31, 32, 39, 40, 53, 54, 55, 63, 64, 65, 71]
    [vertices,colortable,names] = nb.freesurfer.read_annot(freesurferdir+'/fsaverage4/label/'+hemi[-2:]+'.aparc.a2009s.annot', orig_ids=True)
    chosenvertices = list()
    for j, value in enumerate(vertices) :
        for i, index in enumerate(labellist) :
            if colortable[index][4]==value :
                chosenvertices.append(j)
    return chosenvertices

lhvertices = getvertices('lh',freesurferdir)
rhvertices = getvertices('rh',freesurferdir)

hemispheres = ['lh', 'rh']
similarity_types = ['eta2', 'spat', 'temp']
cluster_types = ['spectral', 'hiercluster', 'kmeans', 'dbscan']
n_clusters = [7]
