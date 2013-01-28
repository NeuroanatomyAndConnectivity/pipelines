'''
Created on Nov 7, 2012

@author: gorgolewski
'''


def write_correlation_matrix(in_file, mask_file, out_file):
    import nibabel as nb
    import numpy as np
    from scipy.stats import ss
    import os
    mask_nii = nb.load(mask_file)
    data_nii = nb.load(in_file)
    
    data = data_nii.get_data()[mask_nii.get_data() > 0,:]
    print (data.shape[0]*(data.shape[0]-1)/2)
    return
    
    corr_matrix = np.memmap(out_file, dtype='int16', mode='w+', shape=(data.shape[0]*(data.shape[0]-1)/2))
    
    
    counter = 0
    ms = data.mean(axis=1)[(slice(None,None,None),None)]
    datam = data - ms
    datass = np.sqrt(ss(datam,axis=1))
    
    status = 0
    for i in xrange(0,data.shape[0]):
        temp = np.dot(datam[i+1:],datam[i].T)
        rs = temp / (datass[i+1:]*datass[i])
        corr_matrix[counter:counter+len(rs)] = rs*10000
        counter += len(rs)
        
        if (counter/float(len(corr_matrix)))*100 - status > 1:
            print "%d"%(counter/float(len(corr_matrix))*100)
            status = (counter/float(len(corr_matrix)))*100
        
#    counter = 0
#    for i in range(data.shape[0]):
#        for j in range(i+1, data.shape[0]):
#            print "%g"%(counter/float(data.shape[0]*(data.shape[0]-1)/2))
#            r,_ = pearsonr(data[i,:], data[j,:])
#            corr_matrix[counter] = r
#            counter += 1
    del corr_matrix
    return os.path.abspath(out_file)
            

if __name__ == '__main__':
    write_correlation_matrix("/scr/adenauer1/workingdir/rs_analysis_test/main_workflow/_subject_id_14388.48/_fwhm_5/timeseries2std/corr_20120809_151633t2starepi2Drestings005a001_roi_dtype_detrended_regfilt_smooth_masked_gms_filt_wtsimt.nii.gz", 
                             "/tmp/MNI152_T1_brain_mask_4mm.nii.gz", 
                             "/SCR/tmp/corr_matrix.npy")
        
