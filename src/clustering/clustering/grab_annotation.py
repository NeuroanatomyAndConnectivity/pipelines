import os
import nibabel as nb
from variables import freesurferdir, labellist

def getvertices(hemi, subject_id):
    [vertices,colortable,names] = nb.freesurfer.read_annot(os.path.join(freesurferdir+subject_id+'/label/'+hemi[-2:]+'.aparc.a2009s.annot'), orig_ids=True)
    chosenvertices = list()
    for j, value in enumerate(vertices) :
        for i, index in enumerate(labellist) :
            if colortable[index][4]==value :
                chosenvertices.append(j)
    return chosenvertices
