def build_filter1(motion_params, outliers, comp_norm=None, detrend_poly=None):
    """From https://github.com/nipy/nipype/blob/master/examples/
    rsfmri_vol_surface_preprocessing_nipy.py#L261
    
    Builds a regressor set comprisong motion parameters, composite norm and
    outliers. The outliers are added as a single time point column for each outlier
    
    Parameters
    ----------
    motion_params: a text file containing motion parameters and its derivatives
    comp_norm: a text file containing the composite norm
    outliers: a text file containing 0-based outlier indices
    detrend_poly: number of polynomials to add to detrend
    
    Returns
    -------
    components_file: a text file containing all the regressors
    """
    
    from nipype.utils.filemanip import filename_to_list
    import numpy as np
    import os
    from scipy.special import legendre
    
    out_files = []
    for idx, filename in enumerate(filename_to_list(motion_params)):
        params = np.genfromtxt(filename)
        if comp_norm:
            norm_val = np.genfromtxt(filename_to_list(comp_norm)[idx])
            out_params = np.hstack((params, norm_val[:, None]))
        else:
            out_params = params
        try:
            outlier_val = np.genfromtxt(filename_to_list(outliers)[idx])
        except IOError:
            outlier_val = np.empty((0))
        for index in np.atleast_1d(outlier_val):
            outlier_vector = np.zeros((out_params.shape[0], 1))
            outlier_vector[index] = 1
            out_params = np.hstack((out_params, outlier_vector))
        if detrend_poly:
            timepoints = out_params.shape[0]
            X = np.ones((timepoints, 1))
            for i in range(detrend_poly):
                X = np.hstack((X, legendre(
                    i + 1)(np.linspace(-1, 1, timepoints))[:, None]))
            out_params = np.hstack((out_params, X))
        filename = os.path.join(os.getcwd(), "mcart_regressor.txt") #"filter_regressor%02d.txt" % idx)
        np.savetxt(filename, out_params, fmt="%.10f")
        out_files.append(filename)
    return out_files