import numpy as np
import nibabel as nb
from scipy import stats
from nipy.modalities.fmri.glm import GeneralLinearModel

beh_data = np.recfromcsv('/home/raid3/gorgolewski/Downloads/DataForChris_10_30_12.csv')

#corr_mmaps = []
#for name in beh_data['sub_id_database_brain']:
#    filename = "/scr/adenauer1/workingdir/rs_analysis_test/main_workflow/_subject_id_%s/_fwhm_5/corr_matrix/corr_matrix.int16"%name
#    mmap = np.memmap(filename, dtype='int16', mode='r')
#    corr_mmaps.append(mmap)

filename = "/SCR/tmp/memory_z_map.float64"
z_map = np.memmap(filename, dtype='float64', mode='r')
    
initial_mask_file = "/SCR/MNI152_T1_4mm_brain_mask.nii.gz"
#submask_file = "/SCR/MNI152_T1_4mm_strucseg_periph.nii.gz"
submask_file = "/SCR/memory_4mm.nii.gz"
out_file = "/SCR/all_subjects.int16"

mask_nii = nb.load(initial_mask_file)
initial_mask = mask_nii.get_data() > 0

mask_nii = nb.load(submask_file)
submask = mask_nii.get_data()

submask = submask[initial_mask] > 0

print "%d vs. %d"%(initial_mask.sum(), submask.sum())

#big_map = np.memmap(out_file, dtype='int16', mode='w+', shape=(len(beh_data['sub_id_database_brain']), submask.sum()*(submask.sum()-1)/2))
filename = ""
sub_z_map = np.memmap(filename, dtype='float64', mode='w+', shape=(submask.sum()*(submask.sum()-1)/2))
old_counter = 0
new_counter = 0

for i in xrange(0,initial_mask.sum()):
        for j in xrange(i+1,initial_mask.sum()):
            if submask[j] and submask[i]:
                #for s in range(len(beh_data['sub_id_database_brain'])):
                #    big_map[s,new_counter] = corr_mmaps[s][old_counter]
                sub_z_map[new_counter] = z_map[old_counter]
                new_counter += 1
            old_counter += 1
                