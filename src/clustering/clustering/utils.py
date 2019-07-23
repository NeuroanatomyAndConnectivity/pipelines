import os
import nibabel as nb
import numpy as np

def get_subjects_from(Directory):
    subjects = os.listdir(Directory)
    return subjects

def get_vertices(hemi,freesurferdir, fsaverage, labellist):
    [vertices,colortable,names] = nb.freesurfer.read_annot(os.path.join(freesurferdir,fsaverage+'/label/'+hemi[-2:]+'.aparc.a2009s.annot'), orig_ids=True)
    chosenvertices = list()
    if labellist == []:
        chosenvertices = range(len(vertices)) #all vertices
    else:
        for j, value in enumerate(vertices):
            for i, index in enumerate(labellist):
                if colortable[index][4]==value:
                    chosenvertices.append(j)
    return chosenvertices

def get_mask(labels, parcfile):
    import nibabel as nb
    import numpy as np

    parcdata = nb.load(parcfile).get_data()
    mask = np.zeros_like(parcdata)

    if labels == []:
        mask = parcdata>0
    if labels == [-1]:
        mask = np.zeros_like(parcdata)
    else:
        for label in labels:
            newdata = parcdata == label
            mask = mask + newdata
    return mask
