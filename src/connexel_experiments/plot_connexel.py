'''
Created on Nov 7, 2012

@author: gorgolewski
'''


def plot_connexel(mask_file,idx):
    import nibabel as nb
    import numpy as np
    import pylab as plt
    from nipy.labs.viz_tools.activation_maps import plot_map
    mask_nii = nb.load(mask_file)
    fig = plt.figure(figsize=(8, 4))
    
    beh_data = np.recfromcsv('/home/raid3/gorgolewski/Downloads/DataForChris_10_30_12.csv')

    corr_mmaps = []
    for name in beh_data['sub_id_database_brain']:
        filename = "/scr/adenauer1/workingdir/rs_analysis_test/main_workflow/_subject_id_%s/_fwhm_5/corr_matrix/corr_matrix.int16"%name
        mmap = np.memmap(filename, dtype='int16', mode='r')
        corr_mmaps.append(mmap)
    
    for i, key in enumerate(['mem_meta_d', 'percep_aroc']):
        r_values = np.zeros((len(beh_data[key])))
        for j, corr_mmap in enumerate(corr_mmaps):
            r_values[j] = corr_mmap[idx]
        r_values = np.arctanh(r_values/10000.0)
        ax = plt.subplot2grid((1,2), (0,i))
        ax.scatter(r_values, beh_data[key])
        ax.set_xlabel("normalized_correlation")
        ax.set_ylabel(key)
    plt.savefig("%d_beh_data.pdf"%idx)
    plt.savefig("%d_beh_data.svg"%idx)
    counter = 0
    for i in xrange(0,(mask_nii.get_data() > 0).sum()):
        for j in xrange(i+1,(mask_nii.get_data() > 0).sum()):
            if counter == idx:
                print i,j
                
                new_mask = (np.zeros(mask_nii.get_data().shape) == 1)
                sub_mask = new_mask[mask_nii.get_data() > 0]
                sub_mask[i] = True
                new_mask[mask_nii.get_data() > 0] = sub_mask
                print np.where(new_mask)
                #ax = plt.subplot2grid((2,3), (0,1), colspan=2)
                plot_map(new_mask, mask_nii.get_affine(), threshold='auto')
                plt.savefig("%d_endpoint1.pdf"%idx)
                plt.savefig("%d_endpoint1.svg"%idx)
                
                new_mask = (np.zeros(mask_nii.get_data().shape) == 1)
                sub_mask = new_mask[mask_nii.get_data() > 0]
                sub_mask[j] = True
                new_mask[mask_nii.get_data() > 0] = sub_mask
                print np.where(new_mask)
                #ax = plt.subplot2grid((2,3), (1,1), colspan=2)
                plot_map(new_mask, mask_nii.get_affine(), threshold='auto')
                plt.savefig("%d_endpoint2.pdf"%idx)
                plt.savefig("%d_endpoint2.svg"%idx)
                return

            counter += 1
    print counter

    
            

if __name__ == '__main__':
    import numpy as np
    for contrast_name in ["memory", "perception", "memory>perception"]:
        mmap = np.memmap("/scr/adenauer1/tmp/%s_t_map.float64"%contrast_name, dtype='float64', mode='r')
        idx = np.nanargmin(mmap)
        plot_connexel("/SCR/MNI152_T1_4mm_brain_mask.nii.gz", idx) #364543621)
        idx = np.nanargmax(mmap)
        plot_connexel("/SCR/MNI152_T1_4mm_brain_mask.nii.gz", idx) #364543621)
        
    plt.show()
        
