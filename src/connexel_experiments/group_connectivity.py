import numpy as np
from scipy import stats
from nipy.modalities.fmri.glm import GeneralLinearModel

beh_data = np.recfromcsv('/scr/adenauer1/PowerFolder/Dropbox/papers/meta_cognition/DataForChris_AccScores_4_10_13.csv')

corr_mmaps = []
for name in beh_data['sub_id_database_brain']:
    filename = "/scr/adenauer1/workingdir/rs_analysis_test/main_workflow/_subject_id_%s/_fwhm_5/corr_matrix/corr_matrix.int16"%name
    mmap = np.memmap(filename, dtype='int16', mode='r')
    corr_mmaps.append(mmap)

design_matrix = np.vstack((np.ones(len(beh_data['sub_id_database_brain'])), beh_data['memory_acc'], beh_data['perception_acc'], beh_data['age'])).T
design_matrix[1,:] = stats.zscore(design_matrix[1,:])
design_matrix[2,:] = stats.zscore(design_matrix[2,:])
design_matrix[3,:] = stats.zscore(design_matrix[3,:])

contrasts = 1#, "memory>perception": [0,1,-1,0]}
contrasts_t_mmaps = {}
contrasts_p_mmaps = {}
contrasts_z_mmaps = {}
for contrast_name in contrasts.keys():
    contrasts_t_mmaps[contrast_name] =  np.memmap("/scr/adenauer1/tmp/%s_t_map.float64"%contrast_name, dtype='float64', mode='w+', shape=corr_mmaps[0].shape)
    contrasts_p_mmaps[contrast_name] =  np.memmap("/scr/adenauer1/tmp/%s_p_map.float64"%contrast_name, dtype='float64', mode='w+', shape=corr_mmaps[0].shape)
    contrasts_z_mmaps[contrast_name] =  np.memmap("/scr/adenauer1/tmp/%s_z_map.float64"%contrast_name, dtype='float64', mode='w+', shape=corr_mmaps[0].shape)

glm = GeneralLinearModel(design_matrix)

chunk_size = 40000
print len(corr_mmaps[0])

counter = 0

while counter < len(corr_mmaps[0]):
    data_chunk = np.vstack([(corr_mmaps[i][counter:counter+chunk_size]) for i in range(len(beh_data['sub_id_database_brain']))])
    data_chunk = np.arctanh(data_chunk/10000.0)
    
    glm.fit(data_chunk,model="ols")

    for contrast_name, contrast in contrasts.iteritems():
        c = glm.contrast(contrast)
        contrasts_t_mmaps[contrast_name][counter:counter+chunk_size] = c.stat()
        contrasts_p_mmaps[contrast_name][counter:counter+chunk_size] = c.p_value()
        contrasts_z_mmaps[contrast_name][counter:counter+chunk_size] = c.z_score()
    
    counter += chunk_size
    print "%g"%(counter/float(len(corr_mmaps[0])))
