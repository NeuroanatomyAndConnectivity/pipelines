import nibabel as nb
import numpy as np
import pickle
import sys

inputFile = sys.argv[1]
flag = 'found cluster!!'
rowflag = 'rows=,['

clusters = []
with open(inputFile,'rb') as openfile:
	for line in openfile:
		if line[:len(flag)] == flag:
			clusters.append(line)

for index, cluster in enumerate(clusters):
    words = cluster.split( )
    for x in enumerate(words):
		if x[:len(rowflag)] == rowflag:
            numbers = x[len(rowflag):-2].split(',')

    savefile = '/SCR/Eran/newImage_cluster'+str(index)
    with open(savefile,'wb') as openfile:
	    pickle.dump(vertices, openfile)

#newImage = nb.minc.MincImage(vertices, None)
#nb.save(newImage, savefile)


