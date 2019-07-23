'''
Created on Oct 17, 2013

@author: moreno and kanaan
'''

#!/usr/bin/env python
"""
=============================================
Diffusion MRI Probabiltic tractography on NKI_enhanced.

This script uses FSL and MRTRIX algorithms to generate probabilstic tracts, tract density images
and  a 3D trackvis file of NKI_enhanced data.
=============================================
"""

def do_pipe1_prepro(subject_ID, freesurfer_dir, data_dir, data_template, workflow_dir, output_dir):

    
    """
    Packages and Data Setup
    =======================
    Import necessary modules from nipype.
    """
    
    
    import nipype.interfaces.io as io  # Data i/o
    import nipype.interfaces.utility as util  # utility
    import nipype.pipeline.engine as pe  # pipeline engine
    import nipype.interfaces.fsl as fsl
    import nipype.interfaces.freesurfer as fsurf  # freesurfer
    import nipype.interfaces.mrtrix as mrtrix
    import nipype.interfaces.ants as ants
    import nipype.interfaces.vista as vista
    import os.path as op  # system functions
    
    from nipype.workflows.dmri.fsl.epi import create_eddy_correct_pipeline
    from nipype.interfaces.utility import Function
    
    from dmri_pipe_aux import threshold_bval
    from dmri_pipe_aux import pick_full_ribbon
    from dmri_pipe_aux import get_voxels
    from dmri_pipe_aux import assign_voxel_ids
    from dmri_pipe_aux import get_mean_b0
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Point to the freesurfer subjects directory (Recon-all must have been run on the subjects)
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    subjects_dir = op.abspath(freesurfer_dir)
    fsurf.FSCommand.set_default_subjects_dir(subjects_dir)
    fsl.FSLCommand.set_default_output_type('NIFTI')
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    define the workflow
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    dmripipeline = pe.Workflow(name='pipe1_prepro')
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Use datasource node to perform the actual data grabbing.
    Templates for the associated images are used to obtain the correct images.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    info = dict(dwi=[['subject_id', 'DTI_mx_137.nii.gz']],
                bvecs=[['subject_id', 'DTI_mx_137.bvecs']],
                bvals=[['subject_id', 'DTI_mx_137.bvals']])
    
    datasource = pe.Node(interface=io.DataGrabber(infields=['subject_id'], outfields=info.keys()), name='datasource')
    datasource.inputs.subject_id =  subject_ID
    datasource.inputs.template = data_template
    datasource.inputs.base_directory = data_dir
    datasource.inputs.template_args = info
    datasource.inputs.sort_filelist = True
    datasource.run_without_submitting = True
    
    auxsource = pe.Node(interface=io.DataGrabber(outfields=['lateral_line']), name='auxsource')
    auxsource.inputs.template = 'lateral_line.nii'
    auxsource.inputs.base_directory = data_dir
    auxsource.inputs.sort_filelist = True
    auxsource.run_without_submitting = True

    
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    The input node and Freesurfer sources declared here will be the main
    conduits for the raw data to the rest of the processing pipeline.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    inputnode = pe.Node(interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals", "lateral_line"]), name="inputnode")
    
    FreeSurferSource = pe.Node(interface=io.FreeSurferSource(), name='01_FreeSurferSource')
    FreeSurferSource.inputs.subjects_dir = subjects_dir
    FreeSurferSource.inputs.subject_id = subject_ID
    FreeSurferSource.run_without_submitting = True
    
 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Define a function that thresholds the bvals and zero's the 'near zero' B images.
    This is a correction for the NKI DWI data. The Bval file has nine 'near zero' B images.
    If this is not corrected, MRTRIX does not read these images as B0's introducing various
    errors throughout the processing
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    corrected_bvalues = pe.Node (name='01_corrected_bvalues', interface=Function (input_names=['in_file', 'thr'], output_names=['out_file'], function=threshold_bval))
    corrected_bvalues.inputs.thr = 100
    corrected_bvalues.run_without_submitting = True
    dmripipeline.connect(inputnode, "bvals", corrected_bvalues, "in_file")
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Diffusion processing nodes
    --------------------------
    
    MRTRIX ENCODING
    Convert FSL format files bvecs and bvals into single encoding file for MRtrix
    invert x axis to get the right convention
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    fsl2mrtrix = pe.Node(interface=mrtrix.FSL2MRTrix(), name='01_fsl2mrtrix')
    fsl2mrtrix.inputs.invert_x = True
    fsl2mrtrix.run_without_submitting = True
    dmripipeline.connect(corrected_bvalues, "out_file", fsl2mrtrix, "bval_file")
    dmripipeline.connect(inputnode, "bvecs", fsl2mrtrix, "bvec_file")
    
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    EDDY CURRENT CORRECTION
    Correct for distortions induced by eddy currents before fitting the tensors.
    The first image  is used as a reference for which to warp the others.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    eddy_corrected_dmri = create_eddy_correct_pipeline(name='01_eddy_corrected_dmri')
    eddy_corrected_dmri.inputs.inputnode.ref_num = 0
    eddy_corrected_dmri.run_without_submitting = True
    dmripipeline.connect(inputnode, "dwi", eddy_corrected_dmri, "inputnode.in_file")

    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    TENSOR FITTING
    Tensors are fitted to each voxel in the diffusion-weighted image and from these three maps are created:
        * Major eigenvector in each voxel
        * Apparent diffusion coefficient
        * Fractional anisotropy
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    dwi2tensor = pe.Node(interface=mrtrix.DWI2Tensor(), name='02_dwi2tensor')
    dwi2tensor.inputs.out_filename=subject_ID +'_tensor.mif'
    dwi2tensor.run_without_submitting = True
    dmripipeline.connect(eddy_corrected_dmri, "outputnode.eddy_corrected", dwi2tensor, "in_file")
    dmripipeline.connect(fsl2mrtrix, "encoding_file", dwi2tensor, "encoding_file")
    
    
    #tensor2vector = pe.Node(interface=mrtrix.Tensor2Vector(), name='03_tensor2vector')
    #dmripipeline.connect([(dwi2tensor, tensor2vector, [['tensor', 'in_file']])])
    #tensor2adc = pe.Node(interface=mrtrix.Tensor2ApparentDiffusion(), name='03_tensor2adc')
    #dmripipeline.connect([(dwi2tensor, tensor2adc, [['tensor', 'in_file']]   )])
    
    tensor_full_fa = pe.Node(interface=mrtrix.Tensor2FractionalAnisotropy(), name='03_tensor2fa')
    tensor_full_fa.run_without_submitting = True
    #full_fa.inputs.out_filename=subject_ID+'_fa_full.nii'
    dmripipeline.connect(dwi2tensor, 'tensor', tensor_full_fa, 'in_file')
    
    full_fa = pe.Node(interface=mrtrix.MRConvert(), name='04_full_fa')
    full_fa.inputs.out_filename = subject_ID + '_fa_full.nii'
    full_fa.inputs.extension = 'nii'
    full_fa.run_without_submitting = True
    dmripipeline.connect(tensor_full_fa, "FA", full_fa, "in_file")
    
    
    mean_b0 = pe.Node(interface=Function(input_names=["bvals_file","dwi_file","out_filename"],output_names=["out_file"],function=get_mean_b0), name='02_mean_b0')
    mean_b0.inputs.out_filename= subject_ID +'_mean_b0.nii'
    mean_b0.run_without_submitting = True
    dmripipeline.connect(eddy_corrected_dmri, "outputnode.eddy_corrected", mean_b0, "dwi_file")
    dmripipeline.connect(corrected_bvalues, "out_file", mean_b0, "bvals_file")
    
    corrected_b0 = pe.Node(interface=ants.N4BiasFieldCorrection(), name='03_corrected_b0')
    corrected_b0.inputs.output_image = subject_ID + '_corrected_b0.nii'
    corrected_b0.inputs.dimension = 3
    corrected_b0.inputs.bspline_fitting_distance = 300
    corrected_b0.inputs.shrink_factor = 3
    corrected_b0.inputs.n_iterations = [50,50,30,20]
    corrected_b0.inputs.convergence_threshold = 1e-6
    corrected_b0.run_without_submitting = True
    dmripipeline.connect(mean_b0, "out_file", corrected_b0, "input_image")    
    
    ''' DISCONTINUED
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    B0_MASK
    This block creates the rough brain mask with two erosion steps. The mask will be used to generate an Single fiber voxel mask
    for the estimation of the response function and a white matter mask which will serve as a seed for tractography.
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    

    bet_b0 = pe.Node(interface=fsl.BET(mask=False), name='02_bet_b0')
    bet_b0.run_without_submitting = True
    dmripipeline.connect(eddy_corrected_dmri, "pick_ref.out", bet_b0, "in_file")
    
    
    b0_mask = pe.Node(interface=fsl.maths.MathsCommand(), name='03_b0_mask')
    b0_mask.inputs.args = '-bin'
    b0_mask.run_without_submitting = True
    dmripipeline.connect(bet_b0, "out_file", b0_mask , "in_file")
    
    """
    mask fa with b0 ... also erode it to use for estimation of response function
    """
    fa_b0_masked = pe.Node(interface=fsl.maths.ApplyMask(), name='05_fa_B0_masked')
    fa_b0_masked.run_without_submitting = True
    dmripipeline.connect(full_fa, "converted", fa_b0_masked, "in_file")
    dmripipeline.connect(b0_mask, "out_file", fa_b0_masked, "mask_file")
    
    fa_b0_masked_ero = pe.Node(interface=fsl.maths.MathsCommand(), name='06_fa_B0_masked_ero')
    fa_b0_masked_ero.inputs.args = '-ero'
    fa_b0_masked_ero.run_without_submitting = True
    dmripipeline.connect(fa_b0_masked, 'out_file', fa_b0_masked_ero, 'in_file')
    '''
    
    
    """
    CSF mask extraction from B0
    """
    CSF_mask = pe.Node(interface=fsl.maths.MathsCommand(), name='02_CSF_mask')
    CSF_mask.inputs.args = '-thrP 95 -binv'
    CSF_mask.inputs.out_file = subject_ID + '_csf_mask.nii'
    CSF_mask.run_without_submitting = True
    dmripipeline.connect(corrected_b0, 'output_image', CSF_mask, 'in_file')
    
        
    
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Non-linear transformation of Fa map onto T1. This will generate a warp field that will be inverted to warp full t1 onto FA.
    
    
    1- Convert ribbon, T1 freesurfer outputs to nii
    2- Mask T1 with ribbon to extract the brain and get rid of the of the CB and BS.
    4- T1 --> FA ---- Register ribbon masked T1 onto B0 masked FA with 6DOFs, cross corr.
    5- Close holes in T1_2_FA_6DOF (-dil -ero)
    6- Mask original FA map with 6DOF FA registered,closed wholes T1.
    7- Eroded FA -ero with default-kbox 3x3x3
    8- Non-linearly transform t1, wm mask created from ribbon
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    """
    convert t1and ribbon to nii
    """
    t1_nii = pe.Node(interface=fsurf.MRIConvert(), name='05_t1_nii')
    t1_nii.inputs.out_type = 'nii'
    t1_nii.inputs.out_file = subject_ID + '_t1.nii'
    t1_nii.run_without_submitting = True
    dmripipeline.connect([(FreeSurferSource, t1_nii, [("T1", "in_file")])])
    
    """
    convert T1 and ribbon
    """
    ribbon_nii = pe.Node(interface=fsurf.MRIConvert(), name='06_ribbon_nii')
    ribbon_nii.inputs.out_file = subject_ID + '_ribbon.nii'
    ribbon_nii.inputs.out_type = 'nii'
    ribbon_nii.run_without_submitting = True
    dmripipeline.connect([(FreeSurferSource, ribbon_nii, [(("ribbon", pick_full_ribbon), "in_file")])])
    
    
    aseg_nii = pe.Node(interface=fsurf.MRIConvert(), name='07_aseg_nii')
    aseg_nii.inputs.out_file = subject_ID + '_aseg.nii'
    aseg_nii.inputs.out_type = 'nii'
    aseg_nii.run_without_submitting = True
    dmripipeline.connect([(FreeSurferSource, aseg_nii, [("aseg", "in_file")])])
    
    """
    mask t1 with ribbon and aseg (without and with cerebellum)
    """
    t1_ribbon_masked = pe.Node(interface=fsl.maths.ApplyMask(), name='08_t1_ribbon_masked')
    t1_ribbon_masked.run_without_submitting = True
    dmripipeline.connect([(t1_nii, t1_ribbon_masked , [("out_file", "in_file")])])
    dmripipeline.connect([(ribbon_nii, t1_ribbon_masked , [("out_file", "mask_file")])])
    
    t1_aseg_masked = pe.Node(interface=fsl.maths.ApplyMask(), name='09_t1_aseg_masked')
    t1_aseg_masked.run_without_submitting = True
    dmripipeline.connect([(t1_nii, t1_aseg_masked , [("out_file", "in_file")])])
    dmripipeline.connect([(aseg_nii, t1_aseg_masked , [("out_file", "mask_file")])])
    
    """
    register T1_aseg_masked to full b0
    """
    flirt_t1aseg_2_b0 = pe.Node(interface=fsl.FLIRT(), name='10_flirt_t1aseg_2_b0')
    flirt_t1aseg_2_b0.inputs.dof = 6
    flirt_t1aseg_2_b0.inputs.cost_func = 'corratio'
    flirt_t1aseg_2_b0.inputs.bins = 256
    flirt_t1aseg_2_b0.inputs.interp = 'trilinear'
    flirt_t1aseg_2_b0.inputs.out_matrix_file = 'flirt_t1_2_b0.mat'
    flirt_t1aseg_2_b0.run_without_submitting = True
    dmripipeline.connect([(t1_ribbon_masked, flirt_t1aseg_2_b0 , [("out_file", "in_file")])])
    dmripipeline.connect([(corrected_b0, flirt_t1aseg_2_b0 , [("output_image", "reference")])])
    
    """
    use warp to convert ribbon to b0
    """
    ribbon_linear2b0 = pe.Node(interface=fsl.ApplyXfm(), name='11_ribbon_linear2b0')
    ribbon_linear2b0.inputs.apply_xfm = True
    ribbon_linear2b0.inputs.interp = 'nearestneighbour'
    ribbon_linear2b0.run_without_submitting = True
    dmripipeline.connect([(ribbon_nii, ribbon_linear2b0 , [("out_file", "in_file")])])
    dmripipeline.connect([(flirt_t1aseg_2_b0, ribbon_linear2b0 , [("out_matrix_file", "in_matrix_file")])])
    dmripipeline.connect([(corrected_b0, ribbon_linear2b0 , [("output_image", "reference")])])
    
    """
    close holes in registered ribbon2b0
    """
    ribbonmask_linear2b0_rounded = pe.Node(interface=fsl.maths.MathsCommand(), name='11_ribbonmask_linear2b0_rounded')
    ribbonmask_linear2b0_rounded.inputs.args = '-bin -kernel sphere 3 -dilM -dilM  -ero -ero -ero'
    ribbonmask_linear2b0_rounded.run_without_submitting = True
    dmripipeline.connect([(ribbon_linear2b0, ribbonmask_linear2b0_rounded, [('out_file', 'in_file')])])
    
    """
    mask fa with registered ribbon
    """
    fa_rib2b0_masked = pe.Node(interface=fsl.maths.ApplyMask(), name='12_fa_t12B0_masked')
    fa_rib2b0_masked.run_without_submitting = True
    dmripipeline.connect(full_fa, "converted", fa_rib2b0_masked, "in_file")
    dmripipeline.connect(ribbonmask_linear2b0_rounded, "out_file", fa_rib2b0_masked, "mask_file")
    
    
    
    """
    register T1_ribbon_masked to Fa_b0_masked
    # flirt -in T1_masked.nii.gz -ref  fa_brain.nii.gz -out t12fa -omat t12fa.mat -bins 256 -cost corratio -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 6  -interp trilinear
    """
    flirt_t1masked_2_FAmasked = pe.Node(interface=fsl.FLIRT(), name='13_flirt_t1m_2_FAm')
    flirt_t1masked_2_FAmasked.inputs.dof = 6
    flirt_t1masked_2_FAmasked.inputs.cost_func = 'corratio'
    flirt_t1masked_2_FAmasked.inputs.bins = 256
    flirt_t1masked_2_FAmasked.inputs.interp = 'trilinear'
    flirt_t1masked_2_FAmasked.inputs.out_matrix_file = 'flirt_t1_2_fa.mat'
    flirt_t1masked_2_FAmasked.run_without_submitting = True
    dmripipeline.connect([(t1_ribbon_masked, flirt_t1masked_2_FAmasked , [("out_file", "in_file")])])
    dmripipeline.connect([(fa_rib2b0_masked, flirt_t1masked_2_FAmasked , [("out_file", "reference")])])
    
    """
    inverse the linear T1 to FA transform
    """
    invert_linearxfm_t1_2_fa = pe.Node(interface=fsl.ConvertXFM(), name='13_invertxfm_t1m_2_FAm')
    invert_linearxfm_t1_2_fa.inputs.invert_xfm = True
    invert_linearxfm_t1_2_fa.inputs.out_file = 'flirt_t1_2_fa_inv.mat'
    invert_linearxfm_t1_2_fa.run_without_submitting = True
    dmripipeline.connect([(flirt_t1masked_2_FAmasked, invert_linearxfm_t1_2_fa , [("out_matrix_file", "in_file")])])
    
    """
    use warp to convert ribbon (again)
    """
    ribbon_linear2fa = pe.Node(interface=fsl.ApplyXfm(), name='14_ribbon_linear2fa')
    ribbon_linear2fa.inputs.apply_xfm = True
    ribbon_linear2fa.inputs.interp = 'nearestneighbour'
    ribbon_linear2fa.run_without_submitting = True
    dmripipeline.connect([(ribbon_nii, ribbon_linear2fa , [("out_file", "in_file")])])
    dmripipeline.connect([(flirt_t1masked_2_FAmasked, ribbon_linear2fa , [("out_matrix_file", "in_matrix_file")])])
    dmripipeline.connect([(fa_rib2b0_masked, ribbon_linear2fa , [("out_file", "reference")])])
    
    """
    close holes in registered ribbon2Fa
    """
    ribbonmask_linear2fa_rounded = pe.Node(interface=fsl.maths.MathsCommand(), name='14_ribbonmask_linear2fa_rounded')
    ribbonmask_linear2fa_rounded.inputs.args = '-bin -kernel sphere 3 -dilM -dilM  -ero -ero -ero'
    ribbonmask_linear2fa_rounded.run_without_submitting = True
    dmripipeline.connect([(ribbon_linear2fa, ribbonmask_linear2fa_rounded, [('out_file', 'in_file')])])
    
    """
    mask full fa with T12Fa_closed_holes
    """
    fa_linear_ribbon_masked = pe.Node(interface=fsl.ApplyMask(), name='15_fa_linear_ribbon_masked')
    fa_linear_ribbon_masked.run_without_submitting = True
    dmripipeline.connect([(full_fa, fa_linear_ribbon_masked , [("converted", "in_file")])])
    dmripipeline.connect([(ribbonmask_linear2fa_rounded, fa_linear_ribbon_masked, [("out_file", "mask_file")])])
    
    """
    Non-linearly transform FA_masked T1_ribbon_masked
    ANTS 3 -m PR[T1_masked.nii,FA_2_T1_6DOF.nii.gz,1,3] -i 5x5 -o FA_2_T1_ANTS.nii.gz -t SyN[0.25] -r Gauss[3,0]
    """
    ants_FA2T1m_2_T1_full = pe.Node(interface=ants.ANTS(), name='16_ants_fa_2_t1')
    ants_FA2T1m_2_T1_full.inputs.dimension = 3
    ants_FA2T1m_2_T1_full.inputs.metric = ['PR']
    ants_FA2T1m_2_T1_full.inputs.radius = [3]
    ants_FA2T1m_2_T1_full.inputs.metric_weight = [1.0]
    ants_FA2T1m_2_T1_full.inputs.transformation_model = 'SyN'
    ants_FA2T1m_2_T1_full.inputs.gradient_step_length = 0.25
    ants_FA2T1m_2_T1_full.inputs.number_of_iterations = [ 5, 5]
    ants_FA2T1m_2_T1_full.inputs.regularization = 'Gauss'
    ants_FA2T1m_2_T1_full.inputs.regularization_gradient_field_sigma = 3
    ants_FA2T1m_2_T1_full.inputs.regularization_deformation_field_sigma = 0
    ants_FA2T1m_2_T1_full.inputs.output_transform_prefix = 'ants_fa_2_regt1_'
    ants_FA2T1m_2_T1_full.run_without_submitting = True
    dmripipeline.connect([(fa_linear_ribbon_masked, ants_FA2T1m_2_T1_full, [('out_file', 'moving_image')])])
    dmripipeline.connect([(flirt_t1masked_2_FAmasked, ants_FA2T1m_2_T1_full, [('out_file', 'fixed_image')])])
        
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Creation of masks for seeding
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    """
    # warp T1_masked to Fa_masked
    """
    t1_warped_2_fa = pe.Node (interface=ants.WarpImageMultiTransform(), name='21_t1_warped_2_fa')
    t1_warped_2_fa.run_without_submitting = True
    dmripipeline.connect([(flirt_t1masked_2_FAmasked, t1_warped_2_fa, [('out_file', 'input_image')])])
    dmripipeline.connect([(fa_linear_ribbon_masked, t1_warped_2_fa, [('out_file', 'reference_image')])])
    dmripipeline.connect([(ants_FA2T1m_2_T1_full, t1_warped_2_fa, [('inverse_warp_transform', 'transformation_series')])])
    
    """
    # warp ribbon 2 fa
    """
    ribbon_warped_2_fa = pe.Node (interface=ants.WarpImageMultiTransform(), name='21_ribbon_warped_2_fa')
    ribbon_warped_2_fa.inputs.use_nearest = True
    ribbon_warped_2_fa.run_without_submitting = True
    dmripipeline.connect([(ribbon_linear2fa, ribbon_warped_2_fa, [('out_file', 'input_image')])])
    dmripipeline.connect([(fa_linear_ribbon_masked, ribbon_warped_2_fa, [('out_file', 'reference_image')])])
    dmripipeline.connect([(ants_FA2T1m_2_T1_full, ribbon_warped_2_fa, [('inverse_warp_transform', 'transformation_series')])])
    
    """
    close holes in registered ribbon2Fa
    """
    ribbon_warped_2_fa_shell = pe.Node(interface=fsl.maths.MathsCommand(), name='21_ribbon_warped_2_fa_shell')
    ribbon_warped_2_fa_shell.inputs.args = '-bin -kernel sphere 3 -dilM -dilM  -ero -ero -ero'
    ribbon_warped_2_fa_shell.run_without_submitting = True
    dmripipeline.connect([(ribbon_warped_2_fa, ribbon_warped_2_fa_shell, [('output_image', 'in_file')])])
    
    
    """
    # generate white matter mask and full brain mask from ribbon
    """
    ribbon_wm_right = pe.Node(interface=fsl.maths.MathsCommand(), name='22_ribbon_right_wm_41')
    ribbon_wm_right.inputs.args = '-thr 41 -uthr 41 -bin'
    ribbon_wm_right.run_without_submitting = True
    dmripipeline.connect([(ribbon_warped_2_fa, ribbon_wm_right, [('output_image', 'in_file')])])
    
    ribbon_gm_right = pe.Node(interface=fsl.maths.MathsCommand(), name='22_ribbon_right_gm_42')
    ribbon_gm_right.inputs.args = '-thr 42 -uthr 42 -bin'
    ribbon_gm_right.run_without_submitting = True
    dmripipeline.connect([(ribbon_warped_2_fa, ribbon_gm_right, [('output_image', 'in_file')])])
    
    ribbon_wm_left = pe.Node(interface=fsl.maths.MathsCommand(), name='22_ribbon_left_wm_2')
    ribbon_wm_left.inputs.args = '-thr 2 -uthr 2 -bin'
    ribbon_wm_left.run_without_submitting = True
    dmripipeline.connect([(ribbon_warped_2_fa, ribbon_wm_left, [('output_image', 'in_file')])])
    
    ribbon_gm_left = pe.Node(interface=fsl.maths.MathsCommand(), name='22_ribbon_left_gm_3')
    ribbon_gm_left.inputs.args = '-thr 3 -uthr 3 -bin'
    ribbon_gm_left.run_without_submitting = True
    dmripipeline.connect([(ribbon_warped_2_fa, ribbon_gm_left, [('output_image', 'in_file')])])
    
    """
    # used masks
    """
    ribbon_fullmask = pe.Node(interface=fsl.maths.MathsCommand(), name='23_ribbon_fullmask')
    ribbon_fullmask.inputs.args = '-bin'
    ribbon_fullmask.inputs.out_file = subject_ID + '_mask_fullbrain.nii'
    ribbon_fullmask.run_without_submitting = True
    dmripipeline.connect([(ribbon_warped_2_fa, ribbon_fullmask, [('output_image', 'in_file')])])
    
    ribbon_left_hemi = pe.Node(interface=fsl.maths.BinaryMaths(), name='23_ribbon_left_hemi')
    ribbon_left_hemi.inputs.operation = 'add'
    ribbon_left_hemi.inputs.args = '-bin'
    ribbon_left_hemi.inputs.out_file = subject_ID + '_mask_left_hemi.nii'
    ribbon_left_hemi.run_without_submitting = True
    dmripipeline.connect([(ribbon_gm_left, ribbon_left_hemi, [('out_file', 'in_file')])])
    dmripipeline.connect([(ribbon_wm_left, ribbon_left_hemi, [('out_file', 'operand_file')])])
    
    ribbon_right_hemi = pe.Node(interface=fsl.maths.BinaryMaths(), name='23_ribbon_right_hemi')
    ribbon_right_hemi.inputs.operation = 'add'
    ribbon_right_hemi.inputs.args = '-bin'
    ribbon_right_hemi.inputs.out_file = subject_ID + '_mask_right_hemi.nii'
    ribbon_right_hemi.run_without_submitting = True
    dmripipeline.connect([(ribbon_gm_right, ribbon_right_hemi, [('out_file', 'in_file')])])
    dmripipeline.connect([(ribbon_wm_right, ribbon_right_hemi, [('out_file', 'operand_file')])])
    
    ribbon_wm_mask = pe.Node(interface=fsl.maths.BinaryMaths(), name='23_ribbon_wm_mask')
    ribbon_wm_mask.inputs.operation = 'add'
    ribbon_wm_mask.inputs.args = '-bin'
    ribbon_wm_mask.run_without_submitting = True
    dmripipeline.connect([(ribbon_wm_right, ribbon_wm_mask, [('out_file', 'in_file')])])
    dmripipeline.connect([(ribbon_wm_left, ribbon_wm_mask, [('out_file', 'operand_file')])])
    
    ribbon_wm_mask_ero = pe.Node(interface=fsl.maths.MathsCommand(), name='23_ribbon_wm_mask_ero')
    ribbon_wm_mask_ero.inputs.args = '-kernel sphere 2 -ero'
    ribbon_wm_mask_ero.run_without_submitting = True
    dmripipeline.connect([(ribbon_wm_mask, ribbon_wm_mask_ero, [('out_file', 'in_file')])])
    
    
    """
    # mask fa with new ribbon
    """
    fa_nl_ribbon_masked = pe.Node(interface=fsl.maths.ApplyMask(), name='24_fa_nl_ribbon_masked')
    fa_nl_ribbon_masked.inputs.out_file = subject_ID + '_fa_masked.nii'
    fa_nl_ribbon_masked.run_without_submitting = True
    dmripipeline.connect([(full_fa, fa_nl_ribbon_masked , [("converted", "in_file")])])
    dmripipeline.connect([(ribbon_fullmask, fa_nl_ribbon_masked , [("out_file", "mask_file")])])
    
    """
    # generate white matter mask from FA with 0.2 thresh
    """
    fa_masked_thresh_bin = pe.Node(interface=fsl.maths.MathsCommand(), name='25_fa_masked_thresh_bin')
    fa_masked_thresh_bin.inputs.args = '-thr 0.2 -bin'
    fa_masked_thresh_bin.run_without_submitting = True
    dmripipeline.connect([(fa_nl_ribbon_masked, fa_masked_thresh_bin, [('out_file', 'in_file')])])
    
    """
    # add fa_wm and ribbon_wm
    """
    fa_wm_holes_closed = pe.Node(interface=fsl.maths.BinaryMaths(), name='26_fa_wm_holes_closed')
    fa_wm_holes_closed.inputs.operation = 'add'
    fa_wm_holes_closed.inputs.args = '-bin'
    fa_wm_holes_closed.run_without_submitting = True
    dmripipeline.connect([(fa_masked_thresh_bin, fa_wm_holes_closed, [('out_file', 'in_file')])])
    dmripipeline.connect([(ribbon_wm_mask_ero, fa_wm_holes_closed, [('out_file', 'operand_file')])])
    
    """
    eliminate non-connected voxels from mask
    """
    fa_wm_connectedcomp_mask = pe.Node(interface=fsl.maths.BinaryMaths(), name='27_fa_wm_connectedcomp_mask')
    fa_wm_connectedcomp_mask.inputs.operation = 'add'
    fa_wm_connectedcomp_mask.inputs.args = '-binv -fillh -binv'
    fa_wm_connectedcomp_mask.run_without_submitting = True
    dmripipeline.connect([(fa_wm_holes_closed, fa_wm_connectedcomp_mask, [('out_file', 'in_file')])])
    dmripipeline.connect([(inputnode, fa_wm_connectedcomp_mask, [('lateral_line', 'operand_file')])])
    
    fa_wm_maincomponent = pe.Node(interface=fsl.maths.ApplyMask(), name='28_fa_wm_maincomponent')
    fa_wm_maincomponent.run_without_submitting = True
    dmripipeline.connect([(fa_wm_holes_closed, fa_wm_maincomponent, [('out_file', 'in_file')])])
    dmripipeline.connect([(fa_wm_connectedcomp_mask, fa_wm_maincomponent , [("out_file", "mask_file")])])
    
    """
    fill holes
    """
    fa_wm_filled = pe.Node(interface=fsl.maths.MathsCommand(), name='29_fa_wm_filled')
    fa_wm_filled.inputs.args = '-fillh'
    fa_wm_filled.run_without_submitting = True
    dmripipeline.connect([(fa_wm_maincomponent, fa_wm_filled , [("out_file", "in_file")])])
    
    """
    remove borders
    """
    fa_wm_rounded = pe.Node(interface=fsl.maths.ApplyMask(), name='29b_wm_rounded')
    fa_wm_rounded.inputs.out_file = subject_ID + '_mask_wm_rounded.nii'
    fa_wm_rounded.run_without_submitting = True
    dmripipeline.connect([(fa_wm_filled, fa_wm_rounded , [("out_file", "in_file")])])
    dmripipeline.connect([(ribbon_warped_2_fa_shell, fa_wm_rounded , [("out_file", "mask_file")])])
    
    """
    exclude csf
    """
    fa_wm_final = pe.Node(interface=fsl.maths.ApplyMask(), name='30_wm_final')
    fa_wm_final.inputs.out_file = subject_ID + '_mask_wm.nii'
    fa_wm_final.run_without_submitting = True
    dmripipeline.connect([(fa_wm_rounded, fa_wm_final , [("out_file", "in_file")])])
    dmripipeline.connect([(CSF_mask, fa_wm_final , [("out_file", "mask_file")])])
    
    """
    save wm in vista format
    """
    wm_vista = pe.Node(interface=vista.Vnifti2Image(), name='30b_wm_vista')
    dmripipeline.connect(fa_wm_final, "out_file", wm_vista, "in_file")
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # INTERFACE
    # create tract seeding interface..
    # ##this is  created by eroding and subtracting this from the non eroded final fa mask
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    fa_wm_ero = pe.Node(interface=fsl.maths.MathsCommand(), name='31_fa_wm_vol_ero')
    fa_wm_ero.inputs.args = '-kernel sphere 2 -ero'
    fa_wm_ero.run_without_submitting = True
    dmripipeline.connect([(fa_wm_rounded, fa_wm_ero, [('out_file', 'in_file')])])
    
    interface_preliminary = pe.Node(interface=fsl.maths.BinaryMaths(), name='32_interface_preliminary')
    interface_preliminary.inputs.operation = 'sub'
    interface_preliminary.run_without_submitting = True
    dmripipeline.connect([(fa_wm_rounded, interface_preliminary, [('out_file', 'in_file')])])
    dmripipeline.connect([(fa_wm_ero, interface_preliminary, [('out_file', 'operand_file')])])
    
    interface_nocsf = pe.Node(interface=fsl.maths.ApplyMask(), name='33_interface_nocsf')
    interface_nocsf.inputs.out_file = subject_ID + '_interface_nocsf.nii'
    interface_nocsf.run_without_submitting = True
    dmripipeline.connect([(interface_preliminary, interface_nocsf , [("out_file", "in_file")])])
    dmripipeline.connect([(fa_wm_final, interface_nocsf , [("out_file", "mask_file")])])
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Creation of Single fiber voxel mask for CSD
    # Create a singla fiber voxel mask
    # this is done by thresholding the the FA MAP at 0.7
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    single_fiber_voxel_mask = pe.Node(interface=fsl.maths.ApplyMask(), name='41_single_fiber_voxel_mask')
    single_fiber_voxel_mask.inputs.args = '-thr 0.7 -bin '
    single_fiber_voxel_mask.inputs.out_file = subject_ID + '_mask_singlefiber.nii'
    single_fiber_voxel_mask.run_without_submitting = True
    dmripipeline.connect([(fa_nl_ribbon_masked, single_fiber_voxel_mask, [('out_file', 'in_file')])])
    dmripipeline.connect([(fa_wm_final, single_fiber_voxel_mask , [("out_file", "mask_file")])])
    
    single_fiber_voxel_mask_mult_final_fa_mif = pe.Node(interface=mrtrix.MRConvert(), name='42_single_fiber_voxel_mask_mult_final_fa_mif')
    single_fiber_voxel_mask_mult_final_fa_mif.inputs.extension = 'mif'
    single_fiber_voxel_mask_mult_final_fa_mif.run_without_submitting = True
    dmripipeline.connect([(single_fiber_voxel_mask, single_fiber_voxel_mask_mult_final_fa_mif, [('out_file', 'in_file')])])
    
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
      Estimation of the response function
     Estimation of the constrained spherical deconvolution depends on the estimate of the response function
     ::For damaged or pathological brains one should take care to lower the maximum harmonic order of these steps.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    estimateresponse = pe.Node(interface=mrtrix.EstimateResponseForSH(), name='43_estimateresponse')
    estimateresponse.inputs.maximum_harmonic_order = 8
    estimateresponse.inputs.out_filename = subject_ID + '_ER.txt'
    dmripipeline.connect([(eddy_corrected_dmri, estimateresponse, [("outputnode.eddy_corrected", "in_file")])])
    dmripipeline.connect([(fsl2mrtrix, estimateresponse, [("encoding_file", "encoding_file")])])
    dmripipeline.connect([(single_fiber_voxel_mask_mult_final_fa_mif, estimateresponse, [("converted", "mask_image")])])
    
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Constrained spherical deconvolution fODF
    - also get direction of the maximum peaks and obtain a f0df max amplitude image, and a threshold of 0.2
    - this will be used to further eliminate noise voxels for the seed image
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    csdeconv = pe.Node(interface=mrtrix.ConstrainedSphericalDeconvolution(), name='44_csdeconv')
    csdeconv.inputs.maximum_harmonic_order = 8
    csdeconv.inputs.out_filename  = subject_ID + '_CSD.mif'
    dmripipeline.connect([(eddy_corrected_dmri, csdeconv, [("outputnode.eddy_corrected", "in_file")])])
    dmripipeline.connect([(fa_wm_final, csdeconv, [("out_file", "mask_image")])])
    dmripipeline.connect([(estimateresponse, csdeconv, [("response", "response_file")])])
    dmripipeline.connect([(fsl2mrtrix, csdeconv, [("encoding_file", "encoding_file")])])
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Detect voxels with odf of less than 0.2 amplitude and obtain a mask of voxels above that value
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    direction_prior = pe.Node(interface=mrtrix.GenerateDirections(), name='45_priordirs')
    direction_prior.inputs.num_dirs = 100
#     direction_prior.inputs.out_file = "directions_100.txt"

    csd_peaks = pe.Node(interface=mrtrix.FindShPeaks(), name='46_csd_peaks')
    csd_peaks.inputs.num_peaks = 1
    csd_peaks.inputs.out_file = subject_ID + '_CSD_peaks.mif'
    dmripipeline.connect(csdeconv, "spherical_harmonics_image", csd_peaks, "in_file")
    dmripipeline.connect(direction_prior, "out_file", csd_peaks, "directions_file")
    
    csd_amplitude = pe.Node(interface=mrtrix.Directions2Amplitude(), name='47_csd_amplitude')
    csd_amplitude.inputs.out_file = subject_ID + '_CSD_amplitude.mif'
    csd_amplitude.run_without_submitting = True
    dmripipeline.connect(csd_peaks, "out_file", csd_amplitude, "in_file")
    
    csd_amplitude_nii = pe.Node(interface=mrtrix.MRConvert(), name='47_csd_amplitude_nii')
    csd_amplitude_nii.inputs.out_filename = subject_ID + '_CSD_amplitude.nii'
    csd_amplitude_nii.inputs.extension = 'nii'
    csd_amplitude_nii.run_without_submitting = True
    dmripipeline.connect(csd_amplitude, "out_file", csd_amplitude_nii, "in_file")
    
    csd_amplitude_mask = pe.Node(interface=fsl.maths.MathsCommand(), name='48_csd_amplitude_mask')
    csd_amplitude_mask.inputs.args = '-thr 0.25 -bin'
    csd_amplitude_mask.inputs.out_file = subject_ID + '_CSD_amplitude_mask025.nii'
    csd_amplitude_mask.run_without_submitting = True
    dmripipeline.connect(csd_amplitude_nii, "converted", csd_amplitude_mask, "in_file")
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Eliminate noisy csf voxels from the mask, eliminate unconnected vioxels and divide the interface for left and right hemisphere
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    interface_denoised = pe.Node(interface=fsl.maths.ApplyMask(), name='50_interface_denoised')
    interface_denoised.inputs.out_file = subject_ID + '_interface_denoised.nii'
    interface_denoised.run_without_submitting = True
    dmripipeline.connect(interface_nocsf, "out_file", interface_denoised, "in_file")
    dmripipeline.connect(csd_amplitude_mask, "out_file", interface_denoised, "mask_file")

    interface_connectedcomp_mask = pe.Node(interface=fsl.maths.BinaryMaths(), name='51_interface_connectedcomp_mask')
    interface_connectedcomp_mask.inputs.operation = 'add'
    interface_connectedcomp_mask.inputs.args = '-binv -fillh26 -binv'
    interface_connectedcomp_mask.run_without_submitting = True
    dmripipeline.connect(interface_denoised,'out_file', interface_connectedcomp_mask,'in_file')
    dmripipeline.connect(inputnode,'lateral_line', interface_connectedcomp_mask, 'operand_file')
    
    interface_all = pe.Node(interface=fsl.maths.ApplyMask(), name='52_interface_all')
    interface_all.inputs.out_file = subject_ID + '_interface_all.nii'
    interface_all.run_without_submitting = True
    dmripipeline.connect(interface_denoised, "out_file", interface_all, "in_file")
    dmripipeline.connect(interface_connectedcomp_mask, "out_file", interface_all, "mask_file")
    
    interface_left = pe.Node(interface=fsl.maths.ApplyMask(), name='53_interface_left')
    interface_left.inputs.out_file = subject_ID + '_interface_left.nii'
    interface_left.run_without_submitting = True
    dmripipeline.connect([(interface_all, interface_left , [("out_file", "in_file")])])
    dmripipeline.connect([(ribbon_left_hemi, interface_left , [("out_file", "mask_file")])])
    
    interface_right = pe.Node(interface=fsl.maths.ApplyMask(), name='53_interface_right')
    interface_right.inputs.out_file = subject_ID + '_interface_right.nii'
    interface_right.run_without_submitting = True
    dmripipeline.connect([(interface_all, interface_right , [("out_file", "in_file")])])
    dmripipeline.connect([(ribbon_right_hemi, interface_right , [("out_file", "mask_file")])])
    
    
    """
    Get the voxel coordinates from the file, and transfrom them to mm coordinates for mrtrix
    text fiels with the coordinates are saved.
    Also, the voxels are ordered by z,y,x. that is, all the voxels in one slice are contigous
    """
    
    interface_voxels_left = pe.Node(interface=Function(input_names=["interface_file","outfile_prefix","return_sample"], output_names=["voxel_file","mm_file","mrtrix_file","voxel_list"], function=get_voxels), name='54_interface_voxels_left')
    interface_voxels_left.inputs.outfile_prefix = subject_ID + '_interface_left'
    interface_voxels_left.run_without_submitting = True
    dmripipeline.connect([(interface_left, interface_voxels_left, [("out_file", "interface_file")])])
    
    interface_voxels_right = interface_voxels_left.clone(name='54_interface_voxels_right')
    interface_voxels_right.inputs.outfile_prefix = subject_ID + '_interface_right'
    dmripipeline.connect([(interface_right, interface_voxels_right, [("out_file", "interface_file")])])
    
    """
    create an image where each seed voxel has a value equal to its id#
    """
    index_image_left = pe.Node(interface=Function(input_names=["in_seed_file","seedvoxel_list","outfile_prefix"],output_names=["out_index_file","index_list"],function=assign_voxel_ids), name='55_index_image_left')
    index_image_left.inputs.outfile_prefix = subject_ID + '_interface_left'
    index_image_left.run_without_submitting = True
    dmripipeline.connect([(interface_left, index_image_left, [("out_file", "in_seed_file")])])
    dmripipeline.connect([(interface_voxels_left, index_image_left, [("voxel_list", "seedvoxel_list")])])
    
    index_image_right = index_image_left.clone(name='55_index_image_right')
    index_image_right.inputs.outfile_prefix = subject_ID + '_interface_right'
    dmripipeline.connect([(interface_right, index_image_right, [("out_file", "in_seed_file")])])
    dmripipeline.connect([(interface_voxels_right, index_image_right, [("voxel_list", "seedvoxel_list")])])

    
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Probabilistic tracking using the obtained fODF
    Pay Attention to the number of tracts sampled from each voxel. Good values are usally in the millions (overall).
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    """
    overal tracking of a small 10000 use_sample in whole white matter to verify data is correct
    """
    probCSDstreamtrack_overall = pe.Node(interface=mrtrix.ProbabilisticSphericallyDeconvolutedStreamlineTrack(), name='61_probCSDstreamtrack_overall')
    probCSDstreamtrack_overall.inputs.inputmodel = 'SD_PROB'
    probCSDstreamtrack_overall.inputs.desired_number_of_tracks = 50000
    probCSDstreamtrack_overall.inputs.maximum_number_of_tracks = 75000
    dmripipeline.connect([(fa_wm_final, probCSDstreamtrack_overall, [("out_file", "mask_file")])])
    dmripipeline.connect([(fa_wm_final, probCSDstreamtrack_overall, [("out_file", "seed_file")])])
    dmripipeline.connect([(csdeconv, probCSDstreamtrack_overall, [("spherical_harmonics_image", "in_file")])])
    
    tracks2prob_overall = pe.Node(interface=mrtrix.Tracks2Prob(), name='62_tracks2prob_overall')
    tracks2prob_overall.inputs.out_filename = subject_ID + '_tract_wm_50000.nii'
    tracks2prob_overall.inputs.voxel_dims= [0.5,0.5,0.5]
    dmripipeline.connect([(probCSDstreamtrack_overall, tracks2prob_overall, [("tracked", "in_file")])])
    #dmripipeline.connect([(fa_wm_final, tracks2prob_overall, [("out_file", "template_file")])])
    

    """
    use a sink to save outputs
    """
    
    datasink = pe.Node(io.DataSink(), name='99_datasink')
    datasink.inputs.base_directory = output_dir
    datasink.inputs.container = subject_ID
    datasink.inputs.parameterization = True
    datasink.run_without_submitting = True
     
    dmripipeline.connect(eddy_corrected_dmri, 'outputnode.eddy_corrected', datasink, 'diff_data')
    dmripipeline.connect(corrected_b0, 'output_image', datasink, 'diff_data.@2')
    dmripipeline.connect(corrected_bvalues, 'out_file', datasink, 'diff_data.@3')
    dmripipeline.connect(fsl2mrtrix, 'encoding_file', datasink, 'diff_data.@4')
    dmripipeline.connect(dwi2tensor, 'tensor', datasink, 'diff_data.@5')
     
    dmripipeline.connect(t1_nii, 'out_file', datasink, 'anatomy')
    dmripipeline.connect(ribbon_nii, 'out_file', datasink, 'anatomy.@2')
    dmripipeline.connect(t1_ribbon_masked, 'out_file', datasink, 'anatomy.@3')
    dmripipeline.connect(flirt_t1masked_2_FAmasked, 'out_file', datasink, 'anatomy.@4')
    dmripipeline.connect(flirt_t1masked_2_FAmasked, 'out_matrix_file', datasink, 'anatomy.@5')
    dmripipeline.connect(ants_FA2T1m_2_T1_full, 'warp_transform', datasink, 'anatomy.@6')
    dmripipeline.connect(ants_FA2T1m_2_T1_full, 'inverse_warp_transform', datasink, 'anatomy.@7')
    dmripipeline.connect(ribbon_warped_2_fa, 'output_image', datasink, 'anatomy.@8')
    dmripipeline.connect(t1_warped_2_fa, 'output_image', datasink, 'anatomy.@9')
    dmripipeline.connect(invert_linearxfm_t1_2_fa, 'out_file', datasink, 'anatomy.@10')
    
     
    dmripipeline.connect(full_fa, 'converted', datasink, 'fa_masking')
    dmripipeline.connect(ribbon_fullmask, 'out_file', datasink, 'fa_masking.@2')
    dmripipeline.connect(ribbon_left_hemi, 'out_file', datasink, 'fa_masking.@3')
    dmripipeline.connect(ribbon_right_hemi, 'out_file', datasink, 'fa_masking.@4')
    dmripipeline.connect(fa_nl_ribbon_masked, 'out_file', datasink, 'fa_masking.@5')
    dmripipeline.connect(fa_wm_final, 'out_file', datasink, 'fa_masking.@6')
    dmripipeline.connect(interface_all, 'out_file', datasink, 'fa_masking.@7')
    dmripipeline.connect(interface_left, 'out_file', datasink, 'fa_masking.@8')
    dmripipeline.connect(interface_right, 'out_file', datasink, 'fa_masking.@9')
    dmripipeline.connect(interface_voxels_left, 'voxel_file', datasink, 'fa_masking.@10')
    dmripipeline.connect(interface_voxels_left, 'mm_file', datasink, 'fa_masking.@11')
    dmripipeline.connect(interface_voxels_left, 'mrtrix_file', datasink, 'fa_masking.@12')
    dmripipeline.connect(interface_voxels_right, 'voxel_file', datasink, 'fa_masking.@13')
    dmripipeline.connect(interface_voxels_right, 'mm_file', datasink, 'fa_masking.@14')
    dmripipeline.connect(interface_voxels_right, 'mrtrix_file', datasink, 'fa_masking.@15') 
    dmripipeline.connect(index_image_left, 'out_index_file', datasink, 'fa_masking.@16')
    dmripipeline.connect(index_image_right, 'out_index_file', datasink, 'fa_masking.@17')
    dmripipeline.connect(wm_vista, 'out_file', datasink, 'fa_masking.@18')
    dmripipeline.connect(CSF_mask, 'out_file', datasink, 'fa_masking.@19')
         
    dmripipeline.connect(single_fiber_voxel_mask, 'out_file', datasink, 'diff_model')
    dmripipeline.connect(estimateresponse, 'response', datasink, 'diff_model.@2')
    dmripipeline.connect(csdeconv, 'spherical_harmonics_image', datasink, 'diff_model.@3') 
    dmripipeline.connect(probCSDstreamtrack_overall, 'tracked', datasink, 'diff_model.@4')
    dmripipeline.connect(tracks2prob_overall, 'tract_image', datasink, 'diff_model.@5')
    dmripipeline.connect(csd_amplitude_nii, 'converted', datasink, 'diff_model.@6')
    dmripipeline.connect(csd_amplitude_mask, 'out_file', datasink, 'diff_model.@7')
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ===============================================================================
    Connecting the workflow
    ===============================================================================
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    
    """
    Create a higher-level workflow
    ------------------------------
    Finally, we create another higher-level workflow to connect our dmripipeline workflow with the info and datagrabbing nodes
    declared at the beginning. Our tutorial is now extensible to any arbitrary number of subjects by simply adding
    their names to the subject list and their data to the proper folders.
    """
    
    connectprepro = pe.Workflow(name="dmri_pipe1_prepro")
    
    connectprepro.base_dir = op.abspath(workflow_dir + "/workflow_"+subject_ID )
    connectprepro.connect([(datasource, dmripipeline, [('dwi', 'inputnode.dwi'),('bvals', 'inputnode.bvals'),('bvecs', 'inputnode.bvecs')]),
                           (auxsource, dmripipeline, [('lateral_line', 'inputnode.lateral_line')])])


    return connectprepro
