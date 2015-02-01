def time_normalizer(in_file, tr):
    '''
    Mean centering and variance normalizing a time series
    '''
    import os
    import nitime.fmri.io as io
    import nibabel as nib
    from nipype.utils.filemanip import fname_presuffix
    
    T= io.time_series_from_file(in_file,normalize='zscore', TR=tr)
    normalized_data = T.data
    
    out_img = nib.Nifti1Image(normalized_data,nib.load(in_file).get_affine())
    out_file = fname_presuffix(in_file, suffix='_norm',newpath=os.getcwd())
    out_img.to_filename(out_file)
    
    return out_file



    
    
    