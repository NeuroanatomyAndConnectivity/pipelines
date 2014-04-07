import os
from clustering.utils import get_vertices, get_subjects_from

basedir = os.path.abspath('/scr/ilz1/nki_enhanced/')
workingdir = os.path.join(basedir,'workingdir')

preprocdir = os.path.join(basedir,'Results/preprocResults')
similaritydir = os.path.join(basedir,'Results/similarityResults')
clusterdir = os.path.join(basedir,'Results/clusterResults')
consensusdir = os.path.join(basedir,'Results/consensusResults')

freesurferdir = os.path.join(basedir,'freesurfer')
niftidir = os.path.join(basedir,'RawData/niftis') #only for preprocessing
dicomdir = os.path.join(basedir,'RawData/dicoms') #only for preprocessing

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
similarity_dg_template = dict(sxfm=os.path.join(preprocdir,'aimivolumes/sxfmout/*%s/_fwhm_0/*%s/*/*.nii'),
                                        volumedata=os.path.join(preprocdir,'aimivolumes/preprocessed_resting/*%s/_fwhm_0/*/*/*.nii.gz'),
                                        regfile=os.path.join(preprocdir,'aimivolumes/func2anat_transform/*%s/*/*%s.mat'),
                                        parcfile=os.path.join(freesurferdir,'*%s/mri/aparc.a2009s+aseg.mgz'),)
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

#subjects = get_subjects_from(directory) # extact a list of subjects from a directory's folder names.

subjects = ['0198985'
#'0102157',  '0115454',  '0123048',  '0132850',  '0142609',  '0154419',  '0164326',  '0172228',  '0182604',  '0195031',
#'0103645',  '0115564',  '0123116',  '0132995',  '0142673',  '0154423',  '0164385',  '0173085',  '0183457',  '0195236',
#'0103872',  '0115684',  '0123173',  '0133436',  '0143484',  '0155419',  '0164900',  '0173286',  '0183726',  '0196198',
#'0105290',  '0115824',  '0123429',  '0133646',  '0144314',  '0155458',  '0165532',  '0173358',  '0184446',  '0196558',
#'0105488',  '0116039',  '0123657',  '0133894',  '0144667',  '0156263',  '0165660',  '0173496',  '0185428',  '0196651',
#'0105521',  '0116065',  '0123971',  '0134505',  '0144702',  '0156678',  '0166009',  '0174363',  '0185676',  '0197456',
#'0106057',  '0116415',  '0124714',  '0134795',  '0146714',  '0157873',  '0166094',  '0174886',  '0185781',  '0197836',
#'0106780',  '0116834',  '0125107',  '0135591',  '0146865',  '0157947',  '0166731',  '0176479',  '0186067',  '0198051',
#'0108184',  '0116842',  '0125762',  '0135671',  '0147122',  '0158411',  '0166987',  '0177330',  '0186277',  '0198130',
#'0108355',  '0117168',  '0126369',  '0136303',  '0148071',  '0158560',  '0167693',  '0177681',  '0186697',  '0198357',
#'0109459',  '0117902',  '0126919',  '0136416',  '0149794',  '0158726',  '0167827',  '0177857',  '0187635',  '0198985',
#'0109727',  '0117964',  '0127665',  '0137073',  '0150062',  '0158744',  '0168007',  '0178174',  '0188199',  '0199155',
#'0109819',  '0118051',  '0127733',  '0137496',  '0150404',  '0159429',  '0168013',  '0178453',  '0188219',  '0199340',
#'0111282',  '0119351',  '0127784',  '0137679',  '0150525',  '0160099',  '0168239',  '0178964',  '0188854',  '0199620',
#'0112249',  '0119866',  '0127800',  '0137714',  '0150589',  '0160872',  '0168357',  '0179005',  '0188939',
#'0112347',  '0120557',  '0130249',  '0138497',  '0150716',  '0161200',  '0168413',  '0179283',  '0189478',
#'0112536',  '0120818',  '0130424',  '0138558',  '0151580',  '0161513',  '0168489',  '0179309',  '0190053',
#'0112828',  '0120859',  '0130678',  '0139212',  '0152189',  '0162251',  '0169007',  '0179454',  '0190501',
#'0113013',  '0121400',  '0131127',  '0139300',  '0152384',  '0162704',  '0169571',  '0179873',  '0192197',
#'0113030',  '0122169',  '0131832',  '0139437',  '0152968',  '0162902',  '0170363',  '0180093',  '0192736',
#'0114008',  '0122512',  '0132049',  '0139480',  '0153114',  '0163059',  '0170636',  '0180308',  '0193358',
#'0114232',  '0122816',  '0132088',  '0141795',  '0153131',  '0163228',  '0171266',  '0181439',  '0194023',
#'0115321',  '0122844',  '0132717',  '0141860',  '0153790',  '0163508',  '0171391',  '0182376',  '0194956'
]

exclude_subjects = ['0021001', '0172228']#0021001- strange morphometry, 0172228- no 1400
subjects = list(set(subjects) - set(exclude_subjects))

sessions = ['mx_645','mx_1400','std_2500']

##ROI LABELS##

#Volume Data#
volume_sourcelabels = [-1]#-1 means No Volume #Example: [12114, 12113] #ctx_rh_G_front_inf-Triangul, ctx_rh_G_front_inf-Orbital
volume_targetlabels = [-1]

#Surface Data#
surface_sourcelabels = [] #empty set [] means all surface vertices
surface_targetlabels = [1, 5, 13, 14, 15, 16, 24, 31, 32, 39, 40, 53, 54, 55, 63, 64, 65, 71] #preFrontal Cortex
lhsource = get_vertices('lh', freesurferdir, surface_sourcelabels)
rhsource = get_vertices('rh', freesurferdir, surface_sourcelabels)
lhvertices = get_vertices('lh', freesurferdir, surface_targetlabels)
rhvertices = get_vertices('rh', freesurferdir, surface_targetlabels)

#Analysis Parameters#
hemispheres = ['lh', 'rh']
similarity_types = ['temp','eta2', 'spat']
cluster_types = ['hiercluster', 'kmeans', 'spectral', 'dbscan']
n_clusters = [6]#[2,3,4,5,6,7,8,10,11,12,13,14,15,16,17,18,19,20,21,22]
epsilon = .03
