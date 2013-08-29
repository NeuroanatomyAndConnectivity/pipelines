import nibabel as nb
import numpy as np
import os
import glob
import sys
from variables import resultsdir, hemispheres, analysis_subjects, analysis_sessions, volumedir

def makeConsensus(in_File):
    clustermap=nb.load(in_File).get_data()
    consensus = np.zeros((len(clustermap),len(clustermap)))
    for j in clustermap:
        for i in clustermap:
            consensus[j] = (clustermap[i] == clustermap[j])
    return consensus

def aggregate(clusters):
    sumConsensus = makeConsensus(clusters[0])
    for i, cluster in enumerate(clusters[1:]):
        print('Cluster '+str(i+1)+' of '+str(len(clusters)))
        eachConsensus = makeConsensus(cluster)
        sumConsensus = sumConsensus+eachConsensus

    totalConsensus = sumConsensus/len(clusters)
    return totalConsensus
    
def saveSurface(consensus, path):
        savepath = os.path.abspath(path)
        os.makedirs(os.path.dirname(savepath))
        nImg = nb.Nifti1Image(consensus, None)
        nb.save(nImg, savepath)
        print(savepath + '    Saved.')

for hemi in hemispheres:
    for session in analysis_sessions:
        for subject in analysis_subjects:
            clusterPath = glob.glob(volumedir+'/clustered/*'+hemi+'*/*'+session+'*/*'+subject+'*/')
            if clusterPath != []:
                clusters = []
                for root, dirs, files in os.walk(clusterPath[0]):
                    for name in files:
                        if name.endswith('.nii'):
                            clusters.append(os.path.join(root, name))
                print(hemi+' '+session+' '+subject)

                savepath = volumedir+'/consensus/'+hemi+'/'+session+'/'+subject + '/Consensus.nii'
                if not os.path.exists(os.path.dirname(savepath)):
                    totalConsensus = aggregate(clusters)
                    saveSurface(totalConsensus, savepath)
