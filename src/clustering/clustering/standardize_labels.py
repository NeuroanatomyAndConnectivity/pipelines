import nibabel as nb
import numpy as np

def separate_clusters(clustermap):
    assignments = np.zeros((clustermap.max()+1,len(clustermap)))
    for label in xrange(clustermap.max()+1):
        assignments[label] = clustermap==label
    return assignments

def find_pair(arr):
    maximum = arr==arr.max() #largest intersection for array
    while maximum.sum() >1: #more than one maximum
        print 'Warning, non-unique clusters/n'+str(arr)
        arr = np.where(1-maximum,arr,-arr) #set duplicate maximums as negative
        maximum = arr==arr.max()#try next maximum
    row = np.where(maximum)[0][0] #what row is that maximum in?
    column = np.where(maximum)[1][0] # what column is that maximum in?
    newarr = arr.copy()
    newarr[row,:] = 0 #prevent that row from being chosen again
    newarr[:,column] = 0 #ditto for columns
    newarr = abs(newarr) #get back duplicate maximum
    return row,column,newarr


def cluster_diff(clustermap1,clustermap2): #non-commutative
    boolmap1 = separate_clusters(clustermap1) #expand out to boolean clusters of n_clusters x surface_vertices
    boolmap2 = separate_clusters(clustermap2)

    n = len(boolmap1) #number of clusters
    intersect = np.zeros((n,n)) 
    for i in xrange(n):
        for j in xrange(n):
            intersect[i,j] = np.sum(boolmap1[i]*boolmap2[j]) #find size of intersecting vertices for every pair of clusters
    
    ##############for k in xrange(n):
    ##############    intersect[:,k] = intersect[:,k]/intersect[:,k].sum() #divided by total intersecting vertices

    pairs = []
    destructive_arr = intersect
    for pair in range(intersect.shape[0]): #choose cluster pairs by finding the largest size of intersecting vertices and then removing this pair from the possibility pairs to choose from. Iterate.
        r,c,destructive_arr = find_pair(destructive_arr)
        pairs.append((r,c))
    t = boolmap1.copy()
    for x in pairs:
        origlabel,newlabel = x
        t[origlabel] = np.where(boolmap1[origlabel],newlabel,0) #reassign the cluster labels to new schema
    clustermap1_stdlabels = t.sum(axis=0) #collapse to one clustermap again

    diff = np.where(clustermap1_stdlabels != clustermap2, (clustermap1_stdlabels,clustermap2), 0) #matrix with dimensions 2 x surface_vertices. When cluster assignments are different, that vertex has two labels, one from map1 and one from map2.
    stability = np.sum(diff[0]!=0) #how similar are the clusters?
    return clustermap1_stdlabels, diff, stability

clustermap2 = nb.load('/scr/ilz1/nki_enhanced/Results/clusterResults/clustered/_hemi_lh/_subject_id_0192736/_sim_temp/_cluster_kmeans/_n_clusters_6/similarity.1D_6_kmeans_lh_clustermap.nii').get_data()
clustermap1 = nb.load('/scr/ilz1/nki_enhanced/Results/clusterResults/clustered/_hemi_lh/_subject_id_0188854/_sim_temp/_cluster_hiercluster/_n_clusters_6/similarity.1D_6_hiercluster_lh_clustermap.nii').get_data()
#clustermap2 = nb.load('/scr/ilz1/nki_enhanced/Results/clusterResults/clustered/_hemi_lh/_subject_id_0188854/_sim_temp/_cluster_kmeans/_n_clusters_6/similarity.1D_6_kmeans_lh_clustermap.nii').get_data()
#intersubject: stability=264 intercluster_method: stability=300 both: stability=
newmap, diffmap, stability = cluster_diff(clustermap1,clustermap2) #apply clustermap2's assignments to clustermap1
