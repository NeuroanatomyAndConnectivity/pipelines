from nipype.pipeline.engine import Node, Workflow, MapNode
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.utility as util
import nipype.algorithms.rapidart as ra
import nipype.interfaces.afni as afni
from noise.motreg import motion_regressors
from noise.motionfilter import build_filter1
from noise.compcor import extract_noise_components
from normalize_timeseries import time_normalizer
from nipype.utils.filemanip import list_to_filename

'''
Main workflow for denoising

Largely based on https://github.com/nipy/nipype/blob/master/examples/
rsfmri_vol_surface_preprocessing_nipy.py#L261
but denoising in anatomical space
'''

def create_denoise_pipeline(name='denoise'):

    # workflow
    denoise = Workflow(name='denoise')

    # Define nodes
    inputnode = Node(interface=util.IdentityInterface(fields=['anat_brain',
                                                              'brain_mask',
                                                              'epi2anat_dat',
                                                              'unwarped_mean',
                                                              'epi_coreg',
                                                              'moco_par',
                                                              'highpass_sigma',
                                                              'lowpass_sigma',
                                                              'tr']),
                        name='inputnode')

    outputnode = Node(interface=util.IdentityInterface(fields=['wmcsf_mask',
                                                               'brain_mask_resamp',
                                                               'brain_mask2epi',
                                                               'combined_motion',
                                                               'outlier_files',
                                                               'intensity_files',
                                                               'outlier_stats',
                                                               'outlier_plots',
                                                               'mc_regressor',
                                                               'mc_F',
                                                               'mc_pF',
                                                               'comp_regressor',
                                                               'comp_F',
                                                               'comp_pF',
                                                               'unfiltered_file',
                                                               'unnormalized_file',
                                                               'normalized_file']),
                     name='outputnode')


    # run fast to get tissue probability classes
    fast = Node(fsl.FAST(), name='fast')
    denoise.connect([(inputnode, fast, [('anat_brain', 'in_files')])])

    # functions to select tissue classes
    def selectindex(files, idx):
        import numpy as np
        from nipype.utils.filemanip import filename_to_list, list_to_filename
        return list_to_filename(np.array(filename_to_list(files))[idx].tolist())

    def selectsingle(files, idx):
        return files[idx]

    # resample tissue classes
    resample_tissue = MapNode(afni.Resample(resample_mode='NN',
                                        outputtype='NIFTI_GZ'),
                              iterfield=['in_file'],
                              name = 'resample_tissue')

    denoise.connect([(inputnode, resample_tissue, [('epi_coreg', 'master')]),
                     (fast, resample_tissue, [(('partial_volume_files', selectindex, [0, 2]), 'in_file')]),
                     ])


    # binarize tissue classes
    binarize_tissue = MapNode(fsl.ImageMaths(op_string='-nan -thr 0.99 -ero -bin'),
                        iterfield=['in_file'],
                        name='binarize_tissue')

    denoise.connect([(resample_tissue, binarize_tissue, [('out_file', 'in_file')]),
                     ])

    # combine tissue classes to noise mask
    wmcsf_mask = Node(fsl.BinaryMaths(operation='add',
                                        out_file='wmcsf_mask_lowres.nii.gz'),
                      name='wmcsf_mask')

    denoise.connect([(binarize_tissue, wmcsf_mask, [(('out_file', selectsingle, 0), 'in_file'),
                                                    (('out_file', selectsingle, 1), 'operand_file')]),
                     (wmcsf_mask, outputnode, [('out_file', 'wmcsf_mask')])])

    # resample brain mask
    resample_brain = Node(afni.Resample(resample_mode='NN',
                                        outputtype='NIFTI_GZ',
                                        out_file='T1_brain_mask_lowres.nii.gz'),
                       name = 'resample_brain')

    denoise.connect([(inputnode, resample_brain, [('brain_mask', 'in_file'),
                                                  ('epi_coreg', 'master')]),
                      (resample_brain, outputnode, [('out_file', 'brain_mask_resamp')])])

    # project brain mask into original epi space fpr quality assessment
    brainmask2epi = Node(fs.ApplyVolTransform(interp='nearest',
                                              inverse=True,
                                              transformed_file='T1_brain_mask2epi.nii.gz',),
                       name = 'brainmask2epi')

    denoise.connect([(inputnode, brainmask2epi, [('brain_mask', 'target_file'),
                                                  ('epi2anat_dat', 'reg_file'),
                                                  ('unwarped_mean', 'source_file')]),
                      (brainmask2epi, outputnode, [('transformed_file', 'brain_mask2epi')])])


    # perform artefact detection
    artefact=Node(ra.ArtifactDetect(save_plot=True,
                                    use_norm=True,
                                    parameter_source='FSL',
                                    mask_type='file',
                                    norm_threshold=1,
                                    zintensity_threshold=3,
                                    use_differences=[True,False]
                                    ),
                 name='artefact')
    artefact.plugin_args={'submit_specs': 'request_memory = 17000'}

    denoise.connect([(inputnode, artefact, [('epi_coreg', 'realigned_files'),
                                            ('moco_par', 'realignment_parameters')]),
                     (resample_brain, artefact, [('out_file', 'mask_file')]),
                     (artefact, outputnode, [('norm_files', 'combined_motion'),
                                             ('outlier_files', 'outlier_files'),
                                             ('intensity_files', 'intensity_files'),
                                             ('statistic_files', 'outlier_stats'),
                                             ('plot_files', 'outlier_plots')])])


    # Compute motion regressors
    motreg = Node(util.Function(input_names=['motion_params', 'order','derivatives'],
                                output_names=['out_files'],
                                function=motion_regressors),
                  name='getmotionregress')
    motreg.plugin_args={'submit_specs': 'request_memory = 17000'}

    denoise.connect([(inputnode, motreg, [('moco_par','motion_params')])])

    # Create a filter to remove motion and art confounds
    createfilter1 = Node(util.Function(input_names=['motion_params', 'comp_norm',
                                                    'outliers', 'detrend_poly'],
                                       output_names=['out_files'],
                                       function=build_filter1),
                         name='makemotionbasedfilter')
    createfilter1.inputs.detrend_poly = 2
    createfilter1.plugin_args={'submit_specs': 'request_memory = 17000'}

    denoise.connect([(motreg, createfilter1, [('out_files','motion_params')]),
                     (artefact, createfilter1, [#('norm_files', 'comp_norm'),
                                                ('outlier_files', 'outliers')]),
                     (createfilter1, outputnode, [('out_files', 'mc_regressor')])
                     ])

    # regress out motion and art confounds
    filter1 = Node(fsl.GLM(out_f_name='F_mcart.nii.gz',
                               out_pf_name='pF_mcart.nii.gz',
                               out_res_name='rest_mc_denoised.nii.gz',
                               demean=True),
                   name='filtermotion')

    filter1.plugin_args={'submit_specs': 'request_memory = 17000'}

    denoise.connect([(inputnode, filter1, [('epi_coreg', 'in_file')]),
                    (createfilter1, filter1, [(('out_files', list_to_filename), 'design')]),
                    (filter1, outputnode, [('out_f', 'mc_F'),
                                           ('out_pf', 'mc_pF')])])


    # create filter with compcor components
    createfilter2 = Node(util.Function(input_names=['realigned_file', 'mask_file',
                                                    'num_components',
                                                    'extra_regressors'],
                                       output_names=['out_files'],
                                       function=extract_noise_components),
                         name='makecompcorfilter')
    createfilter2.inputs.num_components = 6
    createfilter2.plugin_args={'submit_specs': 'request_memory = 17000'}

    denoise.connect([(createfilter1, createfilter2, [(('out_files', list_to_filename),'extra_regressors')]),
                     (filter1, createfilter2, [('out_res', 'realigned_file')]),
                     (wmcsf_mask, createfilter2, [('out_file','mask_file')]),
                     (createfilter2, outputnode, [('out_files','comp_regressor')]),
                     ])

    # regress compcor and other noise components
    filter2 = Node(fsl.GLM(out_f_name='F_noise.nii.gz',
                           out_pf_name='pF_noise.nii.gz',
                           out_res_name='rest2anat_denoised.nii.gz',
                           demean=True),
                   name='filternoise')

    filter2.plugin_args={'submit_specs': 'request_memory = 17000'}

    denoise.connect([(filter1, filter2, [('out_res', 'in_file')]),
                     (createfilter2, filter2, [('out_files', 'design')]),
                     (resample_brain, filter2, [('out_file', 'mask')]),
                     (filter2, outputnode, [('out_f', 'comp_F'),
                                            ('out_pf', 'comp_pF'),
                                            ('out_res', 'unfiltered_file')]),
                     ])

    # bandpass filter denoised file
    bandpass_filter = Node(fsl.TemporalFilter(out_file='rest_denoised_bandpassed.nii.gz'),
                              name='bandpass_filter')

    bandpass_filter.plugin_args={'submit_specs': 'request_memory = 17000'}

    denoise.connect([(inputnode, bandpass_filter,[( 'highpass_sigma','highpass_sigma'),
                                                  ('lowpass_sigma', 'lowpass_sigma')]),
                     (filter2, bandpass_filter, [('out_res', 'in_file')]),
                     (bandpass_filter, outputnode, [('out_file', 'unnormalized_file')])
                     ])


    # # time-normalize scans
    # normalize_time=Node(util.Function(input_names=['in_file','tr'],
    #                                      output_names=['out_file'],
    #                                      function=time_normalizer),
    #                        name='normalize_time')
    #
    # normalize_time.plugin_args={'submit_specs': 'request_memory = 17000'}
    #
    # denoise.connect([(inputnode, normalize_time, [('tr', 'tr')]),
    #                  (bandpass_filter, normalize_time, [('out_file', 'in_file')]),
    #                  (normalize_time, outputnode, [('out_file', 'normalized_file')])
    #                  ])



    return denoise
