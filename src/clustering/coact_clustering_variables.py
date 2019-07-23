import os
from clustering.utils import get_vertices, get_subjects_from

workingdir = os.path.abspath('/scr/kongo2/moreno_nipype/coact_clust_workingdir')


datadir = os.path.abspath('/scr/kongo2/co-activation_output')
clusterdir = os.path.join(datadir, 'clustering_results')
consensusdir = os.path.join(datadir, 'consensus_results')


#INPUT DIRECTORIES#

#clustering#
clustering_dg_template = dict(simmatrix=os.path.join(datadir,'pfc_matrix/%s/pfc_coactmat_%s_%s.nii'),
                                        maskindex=os.path.join(clusterdir,'indices/clustermask_%s_%s.npy'),
                                        targetmask=os.path.join(clusterdir,'indices/targetmask_%s_%s.nii'),
                                        )
clustering_dg_args = dict(simmatrix=[['fs','fs','hemi']],
                                       maskindex=[['fs','hemi']],
                                       targetmask=[['fs','hemi']])
#consensus
consensus_dg_template = dict(all_subjects = os.path.join(clusterdir,'clustered/*/*%s*/*%s*/*%s*/*%s*/*%s*/*'),
                                      )
consensus_dg_args= dict(all_subjects=[['hemi', 'sim', '*', 'cluster', 'n_clusters']])

#SUBJECTS & SESSIONS#

# allsubjects = get_subjects_from(datadir) # extact a list of subjects from a directory's folder names.

#subjects = allsubjects #when testing one subject, use [allsubjects[0]]
#subjects = ["0103872","0105290","0105488","0105521","0106057","0106780","0108184","0108355","0108781","0109459","0109727","0109819"] #when testing one subject, use [allsubjects[0]]
#subjects = ["0111282","0112249","0112347","0112536","0112828","0113013","0113030","0114008","0114232","0115321","0115454","0115564","0115684"] #when testing one subject, use [allsubjects[0]]


##ROI LABELS##

#Volume Data#
volume_sourcelabels = [-1]#-1 means No Volume #Example: [12114, 12113] #ctx_rh_G_front_inf-Triangul, ctx_rh_G_front_inf-Orbital, #from clustering/freesurfercolors!.txt
volume_targetlabels = [-1]

#Surface Data#
surface_sourcelabels = [] #empty set [] means all surface vertices
surface_targetlabels = [1,5,6,7,8,12,13,14,15,16,24,29,31,32,53,54,55,63,64,65,69,70,71] #preFrontal Cortex

#Analysis Parameters#
fsaverage = ['fs5']# ,'fs4']
hemispheres = ['lh', 'rh']
cluster_types = ['kmeans','spectral','hiercluster','dbscan']
#cluster_types = ['hiercluster','dbscan']
n_clusters = [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
epsilon = .03 #parameter for dbscan

n_clusters = [8,9,10]


"""
    all clusterings
"""