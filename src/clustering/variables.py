import os
from clustering.utils import get_vertices, get_subjects_from

workingdir = os.path.abspath('/scr/kongo2/moreno_nipype/fmri_clust_workingdir')

basedir = os.path.abspath('/scr/kongo2/NKI_fMRI_output')
preprocdir = os.path.abspath('/scr/kalifornien1/data/nki_enhanced/preprocessed_fmri/results2500')
similaritydir = os.path.join(basedir,'similarity_results_all_labels')
clusterdir = os.path.join(basedir, 'clustering_results_all_labels')
consensusdir = os.path.join(basedir, 'consensus_results_all_labels')

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
similarity_dg_template = dict(sxfm=os.path.join(preprocdir,'%s/preproc/output/bandpassed/fwhm_6.0/RsfMRI_preprocessed_%s_%s.%s.nii*'),
                                        volumedata=os.path.join(preprocdir,'%s/preproc/output/bandpassed/fwhm_0.0/%s_r00_afni_bandpassed.nii*'),
                                        regfile=os.path.join(preprocdir,'%s/preproc/bbreg/*%s_register.mat'),
                                        parcfile=os.path.join(freesurferdir,'%s/mri/aparc.a2009s+aseg.mgz'))
similarity_dg_args = dict(sxfm=[['subject_id','subject_id', 'fs', 'hemi']],
                                       volumedata=[['subject_id','subject_id']],
                                       regfile=[['subject_id','subject_id']],
                                       parcfile=[['subject_id']])
#clustering#
clustering_dg_template = dict(simmatrix=os.path.join(similaritydir,'similarity/*%s/*%s/*%s/*%s/*.nii'),
                                        maskindex=os.path.join(similaritydir,'maskindex/*%s/*%s/*%s/*%s/*.npy'),
                                        targetmask=os.path.join(similaritydir,'targetmask/*%s/*%s/*%s/*%s/*.nii'))
clustering_dg_args = dict(simmatrix=[['fs','hemi','subject_id', 'sim']],
                                       maskindex=[['fs','hemi','subject_id', 'sim']],
                                       targetmask=[['fs','hemi','subject_id', 'sim']])
#consensus
consensus_dg_template = dict(all_subjects = os.path.join(clusterdir,'clustered/*%s*/*%s*/*%s*/*%s*/*%s*/*'))
consensus_dg_args= dict(all_subjects=[['hemi', 'sim', '*', 'cluster', 'n_clusters']])

#SUBJECTS & SESSIONS#

#allsubjects = get_subjects_from(preprocdir) # extact a list of subjects from a directory's folder names.
allsubjects = []

#subjects = ["0103872","0105290","0105488","0105521","0106057","0106780","0108184","0108355","0108781","0109459","0109727","0109819","0111282","0112249","0112347","0112536","0112828","0113013","0113030","0114008","0114232","0115321","0115454","0115564","0115684","0115824","0116039","0116065","0116415","0116834","0116842","0117168","0117902","0117964","0118051","0119351","0119866"]
#subjects = ["0103872","0105290","0105488","0105521","0106057","0106780","0108184","0108355","0108781","0109459","0109727","0109819"]
#subjects = ["0111282","0112249","0112347","0112536","0112828","0113013","0113030","0114008","0114232","0115321","0115454","0115564","0115684","0115824","0116039","0116065","0116415","0116834","0116842","0117168","0117902","0117964","0118051","0119351","0119866"]
subjects=["0108781"]#,"0117168"]

exclude_subjects = [] # no fmri data for these subjects
subjects = list(set(subjects) - set(exclude_subjects))

sessions = ['tr_2500']#'mx_645','mx_1400',

##ROI LABELS##

#Volume Data#
volume_sourcelabels = [-1]#-1 means No Volume #Example: [12114, 12113] #ctx_rh_G_front_inf-Triangul, ctx_rh_G_front_inf-Orbital, #from clustering/freesurfercolors!.txt
volume_targetlabels = [-1]

#Surface Data#
surface_sourcelabels = [] #empty set [] means all surface vertices
#surface_targetlabels = [] #preFrontal Cortex
#surface_targetlabels = [1,5,6,7,8,12,13,14,15,16,24,29,31,32,53,54,55,63,64,65,69,70,71] #preFrontal Cortex
surface_targetlabels = []

#Analysis Parameters#
fsaverage = ['fsaverage4', 'fsaverage5']
hemispheres = ['lh', 'rh']
similarity_types = ['spat','temp','eta2']
#similarity_types = ['eta2']
cluster_types = ['kmeans','spectral','hiercluster','dbscan']
#cluster_types = ['kmeans','spectral']
#cluster_types = ['hiercluster','dbscan']
n_clusters = [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
epsilon = .03 #parameter for dbscan


"""
spat simmats for 010 011 (except 3 excluded)
    all clusterings
eta2 simmats for 010 011 (except 3 excluded)
    all clusterings
temp simmats for 010 011 (except 3 excluded)
    no clusterings
"""
