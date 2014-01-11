import os
from clustering.utils import get_vertices, get_subjects_from

basedir = os.path.abspath('/scr/murg1')
workingdir = os.path.join(basedir,'clustering/workingdir')

preprocdir = os.path.join(basedir,'alex/results2500')
similaritydir = os.path.join(basedir,'clustering/similarityResults')
clusterdir = os.path.join(basedir,'clustering/clusterResults')
consensusdir = os.path.join(basedir,'clustering/consensusResults')

datadir = os.path.abspath('/scr/kalifornien1/data/nki_enhanced')
freesurferdir = os.path.join(datadir,'freesurfer')
niftidir = os.path.join(datadir,'niftis') #only for preprocessing
dicomdir = os.path.join(datadir,'dicoms') #only for preprocessing

#INPUT DIRECTORIES#
#rs_preprocessing#
rs_preprocessing_dg_template = dict(resting_nifti=os.path.join(niftidir,'*%s*/*%s*'),
                                         t1_nifti=os.path.join(niftidir,'*%s*/anat.nii.gz')
                                        )
rs_preprocessing_dg_args = dict(resting_nifti=[['subject_id', 'session']],
                                        t1_nifti=[['subject_id']]
                                       )
def construct_dicomfiledir(subject_id,session):
    filedir = os.path.join(dicomdir, subject_id + '/session_1/RfMRI_' + session)
    return filedir

#similarity#
similarity_dg_template = dict(sxfm=os.path.join(preprocdir,'%s/preproc/sxfmout/bandpassed/fwhm*/*fsaverage5_%s.nii'),
                                        volumedata=os.path.join(preprocdir,'%s/preproc/output/bandpassed/fwhm*/*.nii.gz'),
                                        regfile=os.path.join(preprocdir,'%s/preproc/bbreg/*%s_register.mat'),
                                        parcfile=os.path.join(freesurferdir,'%s/mri/aparc.a2009s+aseg.mgz'),)
similarity_dg_args = dict(sxfm=[['subject_id', 'hemi']],
                                       volumedata=[['subject_id']],
                                       regfile=[['subject_id','subject_id']],
                                       parcfile=[['subject_id']])
#clustering#
clustering_dg_template = dict(simmatrix=os.path.join(similaritydir,'similarity/*%s/*%s/*%s/*.nii'),
                                        maskindex=os.path.join(similaritydir,'maskindex/*%s/*%s/*%s/*.npy'),
                                        targetmask=os.path.join(similaritydir,'targetmask/*%s/*%s/*%s/*.nii'),
                                        )
clustering_dg_args = dict(simmatrix=[['hemi','subject_id', 'sim']],
                                       maskindex=[['hemi','subject_id', 'sim']],
                                       targetmask=[['hemi','subject_id', 'sim']])
#consensus
consensus_dg_template = dict(all_subjects = os.path.join(clusterdir,'clustered/*%s*/*%s*/*%s*/*%s*/*%s*/*')
                                      )
consensus_dg_args= dict(all_subjects=[['hemi', 'sim', '*', 'cluster', 'n_clusters']])

#SUBJECTS & SESSIONS#

allsubjects = get_subjects_from(preprocdir) # extact a list of subjects from a directory's folder names.

subjects = [allsubjects[0]]

exclude_subjects = ['0021001', '0172228']#0021001- strange morphometry, 0172228- no 1400
subjects = list(set(subjects) - set(exclude_subjects))

sessions = ['tr_2500']#'mx_645','mx_1400',

##ROI LABELS##

#Volume Data#
volume_sourcelabels = [-1]#-1 means No Volume #Example: [12114, 12113] #ctx_rh_G_front_inf-Triangul, ctx_rh_G_front_inf-Orbital
volume_targetlabels = [-1]

#Surface Data#
surface_sourcelabels = [] #empty set [] means all surface vertices
surface_targetlabels = [1, 5, 13, 14, 15, 16, 24, 31, 32, 39, 40, 53, 54, 55, 63, 64, 65, 71] #preFrontal Cortex
lhsource = get_vertices('lh', freesurferdir, 'fsaverage5', surface_sourcelabels)
rhsource = get_vertices('rh', freesurferdir, 'fsaverage5', surface_sourcelabels)
lhvertices = get_vertices('lh', freesurferdir, 'fsaverage5', surface_targetlabels)
rhvertices = get_vertices('rh', freesurferdir, 'fsaverage5', surface_targetlabels)

#Analysis Parameters#
hemispheres = ['lh', 'rh']
similarity_types = ['temp', 'spat'] #'eta2'
cluster_types = ['hiercluster', 'kmeans', 'spectral']#, 'dbscan']
n_clusters = [6]#[2,3,4,5,6,7,8,10,11,12,13,14,15,16,17,18,19,20,21,22]
epsilon = .03
