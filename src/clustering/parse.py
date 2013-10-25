import nibabel as nb
import numpy as np
import pickle
import sys
import surfer.io as surf
from variables import freesurferdir
import os

inputDir = sys.argv[1]
flag = 'found cluster!!'
rowflag = 'rows=,['

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def createSurface(inputFile,hemi):
    [vertices,colortable,names] = surf.read_annot(freesurferdir+'/fsaverage4/label/'+hemi+'.aparc.a2009s.annot', orig_ids=True)
    
    clusters = []
    with open(inputFile,'rb') as openfile:
        for line in openfile:
            if line[:len(flag)] == flag:
                clusters.append(line)

    for index, cluster in enumerate(clusters):
        surface = np.zeros_like(vertices)
        startIndex = cluster.find(rowflag)+len(rowflag)
        stopIndex = cluster.find(']', startIndex)-1
        
        for x in cluster[startIndex:stopIndex].split(','):
            vertex = x.lstrip()
            if vertex.isdigit():
                surface[int(x)%2562] = +1
        savefile = inputFile.split('.')[0]+'_cluster'+str(index)
        newImage = nb.nifti1.Nifti1Image(surface, None)
        nb.save(newImage, savefile)
        #with open(savefile,'wb') as openfile:
        #pickle.dump(numbers, openfile)

for root, dirs, filenames in os.walk(inputDir):
    for f in filenames:
        if f.endswith('.log'):
            hemi = f[:2]
            if hemi == 'De' or hemi == 'te':
                hemi = 'lh'
            print f, hemi
            surface = createSurface(os.path.join(root,f), hemi)
