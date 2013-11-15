import nibabel as nb
import numpy as np

def separate_clusters(clustermap):
    assignments = np.zeros((clustermap.max()+1,len(clustermap)))
    for label in xrange(clustermap.max()+1):
        assignments[label] = clustermap==label
    return assignments

clustermap1 = nb.load('/scr/ilz1/nki_enhanced/Results/clusterResults/clustered/_hemi_lh/_subject_id_0192736/_sim_temp/_cluster_hiercluster/_n_clusters_6/similarity.1D_6_hiercluster_lh_clustermap.nii').get_data()

clustermap2 = nb.load('/scr/ilz1/nki_enhanced/Results/clusterResults/clustered/_hemi_lh/_subject_id_0192736/_sim_temp/_cluster_kmeans/_n_clusters_6/similarity.1D_6_kmeans_lh_clustermap.nii').get_data()

boolmap1 = separate_clusters(clustermap1)
boolmap2 = separate_clusters(clustermap2)

n = len(boolmap1) #number of clusters

a = np.zeros((n,n))
b = np.zeros((n,n))
for i in xrange(n):
    for j in xrange(n):
        a[i,j]= np.sum(boolmap1[i]*boolmap2[j])
        b[i,j] = np.sum(boolmap1[i]-(boolmap1[i]*boolmap2[j]))

def find_pair(arr):
    maximum = arr==arr.max()
    row = np.where(maximum)[0][0]
    column = np.where(maximum)[1][0]
    newarr = arr.copy()
    newarr[row,:] = -1
    newarr[:,column] = -1
    return row,column,newarr

pairs = []
destructive_a = a
for pair in xrange(a.shape[0]):
    r,c,destructive_a = find_pair(destructive_a)
    pairs.append((r,c))
    
t = boolmap1.copy()
for x in pairs:
    origlabel,newlabel = x
    t[origlabel] = np.where(boolmap1[origlabel],newlabel,0)
s = t.sum(axis=0)
