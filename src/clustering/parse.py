import nibabel as nb
import numpy as np
import pickle

clusters = []
flag = 'found cluster!!'
rowflag = 'rows=,['
with open('/home/aimi/session1-0021002-lh.txt','rb') as openfile:
	for line in openfile:
		if line[:len(flag)] == flag:
			clusters.append(line)
vertices = np.zeros(155500)
for index,cluster in enumerate(clusters):
	words = cluster.split( )
	for i,x in enumerate(words):
		if x == rowflag:
			while 1:
				try: end = words[i+1][-2] == ']'
				except IndexError: end = False
				if end == False:
					vertices[np.int(words[i+1])] = index
					i+=1
				if end == True:
					vertices[np.int(words[i+1][:-2])] = index
					break
	
#newImage = nb.minc.MincImage(vertices, None)
savefile = '/home/aimi/newImage'
#nb.save(newImage, savefile)

with open(savefile,'wb') as openfile:
	pickle.dump(vertices, openfile)
