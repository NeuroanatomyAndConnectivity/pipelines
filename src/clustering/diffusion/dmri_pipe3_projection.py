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

def do_pipe3_projection(subject_ID, freesurfer_dir, workflow_dir, output_dir, tract_number, use_sample=False):

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
    import nipype.interfaces.ants as ants
    import os.path as op  # system functions
    
    from nipype.interfaces.utility import Function

    from dmri_pipe_aux import get_connectivity_matrix
    from dmri_pipe_aux import surf2file
    from dmri_pipe_aux import voxels2nii
    from dmri_pipe_aux import normalize_matrix
    from dmri_pipe_aux import interface2surf
    from dmri_pipe_aux import read_voxels
    from dmri_pipe_aux import downsample_matrix
    from dmri_pipe_aux import merge_matrices

    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Point to the freesurfer subjects directory (Recon-all must have been run on the subjects)
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    subjects_dir = op.abspath(freesurfer_dir)
    fsurf.FSCommand.set_default_subjects_dir(subjects_dir)
    fsl.FSLCommand.set_default_output_type('NIFTI')
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    define the workflow
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    dmripipeline = pe.Workflow(name = 'pipe3_projection' )
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Use datasource node to perform the actual data grabbing.
    Templates for the associated images are used to obtain the correct images.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    
    data_template = subject_ID + "/%s/" + "%s" + "%s"
    
    info = dict(wm = [['fa_masking', subject_ID, '_mask_wm.nii']],
                seeds_left = [['fa_masking', subject_ID, '_interface_left_voxels.txt']],
                seeds_right = [['fa_masking', subject_ID, '_interface_right_voxels.txt']],
                index_left = [['fa_masking', subject_ID, '_interface_left_index.nii']],
                index_right = [['fa_masking', subject_ID, '_interface_right_index.nii']],
                fa = [['fa_masking', subject_ID, '_fa_masked.nii']],
                t1 = [['anatomy', subject_ID, '_t1_masked.nii']],
                inv_flirt_mat = [['anatomy', '', 'flirt_t1_2_fa_inv.mat']],
                warp = [['anatomy', '', 'ants_fa_2_regt1_Warp.nii.gz']])
    
    
    datasource = pe.Node(interface=io.DataGrabber(outfields=info.keys()), name='datasource')
    datasource.inputs.template = data_template
    datasource.inputs.base_directory = output_dir
    datasource.inputs.template_args = info
    datasource.inputs.sort_filelist = True
    datasource.run_without_submitting = True
    
    tracts_left_source = pe.Node(interface=io.DataGrabber(outfields=['tracts_left']), name='tracts_left_source')
    tracts_left_source.inputs.template = subject_ID + '/raw_tracts/lh/probtract_*.nii'
    tracts_left_source.inputs.base_directory = output_dir
    tracts_left_source.inputs.sort_filelist = True
    tracts_left_source.run_without_submitting = True
    
    tracts_right_source = pe.Node(interface=io.DataGrabber(outfields=['tracts_right']), name='tracts_right_source')
    tracts_right_source.inputs.template = subject_ID + '/raw_tracts/rh/probtract_*.nii'
    tracts_right_source.inputs.base_directory = output_dir
    tracts_right_source.inputs.sort_filelist = True
    tracts_right_source.run_without_submitting = True
  
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    The input node declared here will be the main
    conduits for the raw data to the rest of the processing pipeline.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    inputnode = pe.Node(interface=util.IdentityInterface(fields=["wm", "seeds_left", "seeds_right", "index_left", "index_right", "fa", "t1", "inv_flirt_mat", "warp", "tracts_left", "tracts_right"]), name="inputnode")
    
    """
    read seed coordinates
    """
   
    interface_voxels_left = pe.Node(interface=Function(input_names=["seed_file","use_sample"], output_names=["seed_list"], function=read_voxels), name='70_interface_voxels_left')
    interface_voxels_left.inputs.use_sample = use_sample
    dmripipeline.connect(inputnode, "seeds_left", interface_voxels_left,"seed_file")
    
    interface_voxels_right = interface_voxels_left.clone(name='70_interface_voxels_right')
    dmripipeline.connect(inputnode, "seeds_right", interface_voxels_right,"seed_file")
    
    """
    Get the direct connectivity matrix
    """
        
    connectivity_matrix = pe.Node(interface=Function(input_names=["tract_list_left", "tract_list_right","voxel_list_left","voxel_list_right","max_value"],
                                                        output_names=["submatrix_left_left","submatrix_left_right","submatrix_right_left","submatrix_right_right","exclusion_list"],
                                                        function=get_connectivity_matrix), name='71_direct_connect_array')
    connectivity_matrix.inputs.max_value = tract_number
    connectivity_matrix.run_without_submitting = True
#    connectivity_matrix.plugin_args={'override_specs': 'requirements = Machine == "kalifornien.cbs.mpg.de"'}
    dmripipeline.connect(inputnode, "tracts_left", connectivity_matrix, "tract_list_left")
    dmripipeline.connect(inputnode, "tracts_right", connectivity_matrix, "tract_list_right")
    dmripipeline.connect(interface_voxels_left, "seed_list", connectivity_matrix, "voxel_list_left")
    dmripipeline.connect(interface_voxels_right, "seed_list", connectivity_matrix, "voxel_list_right")
    
    tract_exclusion_mask = pe.Node(interface=Function(input_names=["voxel_list", "ref_image","outfile"], output_names=["outfile"], function=voxels2nii), name='72_tract_exclusion_mask')
    tract_exclusion_mask.inputs.outfile = subject_ID + '_tractseed_exclusion_mask.nii'
    dmripipeline.connect(inputnode, "wm", tract_exclusion_mask, "ref_image")
    dmripipeline.connect(connectivity_matrix, "exclusion_list", tract_exclusion_mask, "voxel_list")
    
    submatrix_left_left = pe.Node(interface=Function(input_names=["in_array", "max_value","outfile_prefix"], output_names=["mat_matrix_nat","mat_matrix_log","nii_matrix_nat","nii_matrix_log" ], function=normalize_matrix), name='73_submatrix_left_left')
    submatrix_left_left.run_without_submitting = True    
    submatrix_left_left.inputs.max_value = tract_number
    submatrix_left_left.inputs.outfile_prefix = 'directconnect_left_left'
    dmripipeline.connect(connectivity_matrix, "submatrix_left_left", submatrix_left_left, "in_array")
    
    submatrix_left_right = submatrix_left_left.clone(name='73_submatrix_left_right')
    submatrix_left_right.inputs.outfile_prefix = 'directconnect_left_right'
    dmripipeline.connect(connectivity_matrix, "submatrix_left_right", submatrix_left_right, "in_array")
    
    submatrix_right_left = submatrix_left_left.clone(name='73_submatrix_right_left')
    submatrix_right_left.inputs.outfile_prefix = 'directconnect_right_left'
    dmripipeline.connect(connectivity_matrix, "submatrix_right_left", submatrix_right_left, "in_array")
    
    submatrix_right_right = submatrix_left_left.clone(name='73_submatrix_right_right')
    submatrix_right_right.inputs.outfile_prefix = 'directconnect_right_right'
    dmripipeline.connect(connectivity_matrix, "submatrix_right_right", submatrix_right_right, "in_array")
    
#     full_matrix_nat = pe.Node(interface=Function(input_names=["sm_left_left", "sm_left_right","sm_right_left", "sm_right_right", "out_filename"], output_names=["out_file"], function=merge_matrices), name='73_full_matrix_nat')
#     full_matrix_nat.inputs.out_filename = 'directconnect_full_nat.mat'
#     full_matrix_nat.run_without_submitting = True
#     dmripipeline.connect(submatrix_left_left, "nii_matrix_nat", full_matrix_nat, "sm_left_left")
#     dmripipeline.connect(submatrix_left_right, "nii_matrix_nat", full_matrix_nat, "sm_left_right")
#     dmripipeline.connect(submatrix_right_left, "nii_matrix_nat", full_matrix_nat, "sm_right_left")
#     dmripipeline.connect(submatrix_right_right, "nii_matrix_nat", full_matrix_nat, "sm_right_right")
# 
#     full_matrix_log = full_matrix_nat.clone(name='73_full_matrix_log')
#     full_matrix_log.inputs.out_filename = 'directconnect_full_log.mat'
#     full_matrix_log.run_without_submitting = True
#     dmripipeline.connect(submatrix_left_left, "nii_matrix_log", full_matrix_log, "sm_left_left")
#     dmripipeline.connect(submatrix_left_right, "nii_matrix_log", full_matrix_log, "sm_left_right")
#     dmripipeline.connect(submatrix_right_left, "nii_matrix_log", full_matrix_log, "sm_right_left")
#     dmripipeline.connect(submatrix_right_right, "nii_matrix_log", full_matrix_log, "sm_right_right")


    """
    # invert and binarize tract exclusion mask and remove those voxels from the index interfaces
    """
    tract_denoise_mask = pe.Node(interface=fsl.maths.MathsCommand(), name='74_tract_denoise_mask')
    tract_denoise_mask.inputs.args = '-binv'
    tract_denoise_mask.run_without_submitting = True
    dmripipeline.connect(tract_exclusion_mask, "outfile", tract_denoise_mask, "in_file")
    
    index_pruned_left = pe.Node(interface=fsl.maths.ApplyMask(), name='75_interface_pruned_left')
    index_pruned_left.inputs.out_file = subject_ID + '_interface_pruned_left.nii'
    index_pruned_left.run_without_submitting = True
    dmripipeline.connect(inputnode, "index_left", index_pruned_left, "in_file")
    dmripipeline.connect(tract_denoise_mask, "out_file", index_pruned_left, "mask_file")
       
    index_pruned_right = index_pruned_left.clone(name='75_interface_pruned_right')
    index_pruned_right.inputs.out_file = subject_ID + '_interface_pruned_right.nii'
    dmripipeline.connect(inputnode, "index_right", index_pruned_right, "in_file")
    dmripipeline.connect(tract_denoise_mask, "out_file", index_pruned_right, "mask_file")
    
    """
    # warp index image to t1 space
    """
    index_warped_2_t1_left = pe.Node (interface=ants.WarpImageMultiTransform(), name='76_index_warped_2_t1_left')
    index_warped_2_t1_left.inputs.use_nearest = True
    index_warped_2_t1_left.run_without_submitting = True
    dmripipeline.connect([(index_pruned_left, index_warped_2_t1_left, [('out_file', 'input_image')])])
    dmripipeline.connect([(inputnode, index_warped_2_t1_left, [('fa', 'reference_image')])])
    dmripipeline.connect([(inputnode, index_warped_2_t1_left, [('warp', 'transformation_series')])])
    
    index_warped_2_t1_right = index_warped_2_t1_left.clone(name='76_index_warped_2_t1_right')
    dmripipeline.connect([(index_pruned_right, index_warped_2_t1_right, [('out_file', 'input_image')])])
    dmripipeline.connect([(inputnode, index_warped_2_t1_right, [('fa', 'reference_image')])])
    dmripipeline.connect([(inputnode, index_warped_2_t1_right, [('warp', 'transformation_series')])])
    
    index_final_2_t1_left = pe.Node(interface=fsl.ApplyXfm(), name='77_index_final_2_t1_left')
    index_final_2_t1_left.inputs.apply_xfm = True
    index_final_2_t1_left.run_without_submitting = True
    index_final_2_t1_left.inputs.interp = 'nearestneighbour'
    index_final_2_t1_left.inputs.out_file = subject_ID + '_index_seedt1_left.nii'
    dmripipeline.connect([(index_warped_2_t1_left, index_final_2_t1_left , [("output_image", "in_file")])])
    dmripipeline.connect([(inputnode, index_final_2_t1_left , [("inv_flirt_mat", "in_matrix_file")])])
    dmripipeline.connect([(inputnode, index_final_2_t1_left , [("t1", "reference")])])
    
    index_final_2_t1_right = index_final_2_t1_left.clone(name='77_index_final_2_t1_right')
    index_final_2_t1_right.inputs.out_file = subject_ID + '_index_seedt1_right.nii'
    dmripipeline.connect([(index_warped_2_t1_right, index_final_2_t1_right , [("output_image", "in_file")])])
    dmripipeline.connect([(inputnode, index_final_2_t1_right , [("inv_flirt_mat", "in_matrix_file")])])
    dmripipeline.connect([(inputnode, index_final_2_t1_right , [("t1", "reference")])])
    
    """
    extra processing
    """
    

    index_vol2surf_left = pe.Node(interface=fsurf.SampleToSurface(), name='78_index_vol2surf_left')
    index_vol2surf_left.inputs.hemi = 'lh'
    index_vol2surf_left.inputs.subject_id = subject_ID
    index_vol2surf_left.inputs.reg_header = True
    index_vol2surf_left.inputs.interp_method = 'nearest'
    index_vol2surf_left.inputs.sampling_method = 'point'
    index_vol2surf_left.inputs.sampling_range = 0  
    index_vol2surf_left.inputs.sampling_units = 'frac'   
    index_vol2surf_left.inputs.surface = 'orig'
    #index_vol2surf_left.inputs.cortex_mask = True
    index_vol2surf_left.inputs.terminal_output = 'file'
    index_vol2surf_left.inputs.out_file = subject_ID + '_index_seedt1_2surf_left.mgz'
    index_vol2surf_left.run_without_submitting = True
    dmripipeline.connect([(index_final_2_t1_left, index_vol2surf_left, [('out_file', 'source_file')])])
     
    index_vol2surf_right = index_vol2surf_left.clone(name='78_index_vol2surf_right')
    index_vol2surf_right.inputs.hemi = 'rh'
    index_vol2surf_right.inputs.out_file = subject_ID + '_index_seedt1_2surf_right.mgz'
    dmripipeline.connect([(index_final_2_t1_right, index_vol2surf_right, [('out_file', 'source_file')])])
    
    
    index_2_t1_reorient_left = pe.Node(interface=fsl.Reorient2Std(), name='79_next_2_t1_reorient_left')
    index_2_t1_reorient_left.inputs.out_file = subject_ID + '_index_seedt1_reorient_left.nii'
    index_2_t1_reorient_left.run_without_submitting = True
    dmripipeline.connect(index_final_2_t1_left, 'out_file', index_2_t1_reorient_left,  'in_file')
    
    index_2_t1_reorient_right = index_2_t1_reorient_left.clone(name='79_next_2_t1_reorient_right')
    index_2_t1_reorient_right.inputs.out_file = subject_ID + '_index_seedt1_reorient_right.nii'
    dmripipeline.connect(index_final_2_t1_right, 'out_file', index_2_t1_reorient_right,  'in_file')
    
    index_interface2surf_left = pe.Node(interface=Function(input_names=["interface_image", "surface_file","cortex_label","ref_mgz","out_file"], output_names=["out_file"],
                                                        function=interface2surf), name='80_index_interface2surf_left')
    index_interface2surf_left.inputs.surface_file = subjects_dir + '/' + subject_ID + '/surf/lh.orig'
    index_interface2surf_left.inputs.cortex_label = subjects_dir + '/' + subject_ID + '/label/lh.cortex.label'
    index_interface2surf_left.inputs.out_file = subject_ID + '_index_seedt1_2surf_left.mgz'
    dmripipeline.connect(index_2_t1_reorient_left, 'out_file', index_interface2surf_left,  'interface_image')
    dmripipeline.connect(index_vol2surf_left, 'out_file', index_interface2surf_left,  'ref_mgz')
    
    index_interface2surf_right = index_interface2surf_left.clone(name='80_index_interface2surf_right')
    index_interface2surf_right.inputs.surface_file = subjects_dir + '/' + subject_ID + '/surf/rh.orig'
    index_interface2surf_right.inputs.cortex_label = subjects_dir + '/' + subject_ID + '/label/rh.cortex.label'
    index_interface2surf_right.inputs.out_file = subject_ID + '_index_seedt1_2surf_right.mgz'
    dmripipeline.connect(index_2_t1_reorient_right, 'out_file', index_interface2surf_right,  'interface_image')
    dmripipeline.connect(index_vol2surf_right, 'out_file', index_interface2surf_right,  'ref_mgz')
    
    
    fs_indexlist_left = pe.Node(interface=Function(input_names=["in_surface_values","cortex_label","out_file"], output_names=["out_file"], function=surf2file), name='81_index_fsnative_left')
    fs_indexlist_left.inputs.cortex_label = op.join(freesurfer_dir, subject_ID+'/label/lh.cortex.label')
    fs_indexlist_left.inputs.out_file = subject_ID + '_seed_index_fsnative_left.txt'
    fs_indexlist_left.run_without_submitting = True
    dmripipeline.connect([(index_interface2surf_left, fs_indexlist_left, [("out_file", "in_surface_values")])])
    
    fs_indexlist_right = fs_indexlist_left.clone(name='81_index_fsnative_right')
    fs_indexlist_right.inputs.cortex_label = op.join(freesurfer_dir,subject_ID+'/label/rh.cortex.label')
    fs_indexlist_right.inputs.out_file = subject_ID + '_seed_index_fsnative_right.txt'
    dmripipeline.connect([(index_interface2surf_right, fs_indexlist_right, [("out_file", "in_surface_values")])])
    
    """""""""""""""""""""""""""
    """""""""""""""""""""""""""
    
    index_fsaverage5_left = pe.Node(interface=fsurf.SurfaceTransform(), name='81_index_fsaverage5_left')
    index_fsaverage5_left.inputs.hemi = 'lh'
    index_fsaverage5_left.inputs.source_subject = subject_ID
    index_fsaverage5_left.inputs.target_subject = 'fsaverage5'
    index_fsaverage5_left.inputs.args = '--mapmethod nnf --label-src lh.cortex.label --label-trg lh.cortex.label'
    index_fsaverage5_left.inputs.out_file = subject_ID + '_index_seedt1_fsaverage5_left.mgz'
    #index_fsaverage5_left.run_without_submitting = True
    dmripipeline.connect([(index_interface2surf_left, index_fsaverage5_left, [('out_file', 'source_file')])])
    
    index_fsaverage5_right = index_fsaverage5_left.clone(name='81_index_fsaverage5_right')
    index_fsaverage5_right.inputs.hemi = 'rh'
    index_fsaverage5_left.inputs.args = '--mapmethod nnf --label-src rh.cortex.label --label-trg rh.cortex.label'
    index_fsaverage5_right.inputs.out_file = subject_ID + '_index_seedt1_fsaverage5_right.mgz'
    dmripipeline.connect([(index_interface2surf_right, index_fsaverage5_right, [('out_file', 'source_file')])])
    
    fs5_indexlist_left = pe.Node(interface=Function(input_names=["in_surface_values","cortex_label","out_file"], output_names=["out_file"], function=surf2file), name='82_index_fsav5_left')
    fs5_indexlist_left.inputs.cortex_label = op.join(freesurfer_dir,'fsaverage5/label/lh.cortex.label')
    fs5_indexlist_left.inputs.out_file = subject_ID + '_seed_index_fs5_left.txt'
    #fs5_indexlist_left.run_without_submitting = True
    dmripipeline.connect([(index_fsaverage5_left, fs5_indexlist_left, [("out_file", "in_surface_values")])])
    
    fs5_indexlist_right = fs5_indexlist_left.clone(name='82_index_fsav5_right')
    fs5_indexlist_right.inputs.cortex_label = op.join(freesurfer_dir,'fsaverage5/label/rh.cortex.label')
    fs5_indexlist_right.inputs.out_file = subject_ID + '_seed_index_fs5_right.txt'
    dmripipeline.connect([(index_fsaverage5_right, fs5_indexlist_right, [("out_file", "in_surface_values")])])
    
    
    index_fsaverage4_left = pe.Node(interface=fsurf.SurfaceTransform(), name='81_index_fsaverage4_left')
    index_fsaverage4_left.inputs.hemi = 'lh'
    index_fsaverage4_left.inputs.source_subject = subject_ID
    index_fsaverage4_left.inputs.target_subject = 'fsaverage4'
    index_fsaverage4_left.inputs.args = '--mapmethod nnf --label-src lh.cortex.label --label-trg lh.cortex.label'
    index_fsaverage4_left.inputs.out_file = subject_ID + '_index_seedt1_fsaverage4_left.mgz'
    #index_fsaverage4_left.run_without_submitting = True
    dmripipeline.connect([(index_interface2surf_left, index_fsaverage4_left, [('out_file', 'source_file')])])
    
    index_fsaverage4_right = index_fsaverage4_left.clone(name='81_index_fsaverage4_right')
    index_fsaverage4_right.inputs.hemi = 'rh'
    index_fsaverage4_left.inputs.args = '--mapmethod nnf --label-src rh.cortex.label --label-trg rh.cortex.label'
    index_fsaverage4_right.inputs.out_file = subject_ID + '_index_seedt1_fsaverage4_right.mgz'
    dmripipeline.connect([(index_interface2surf_right, index_fsaverage4_right, [('out_file', 'source_file')])])
    
    fs4_indexlist_left = pe.Node(interface=Function(input_names=["in_surface_values","cortex_label","out_file"], output_names=["out_file"], function=surf2file), name='82_index_fsav4_left')
    fs4_indexlist_left.inputs.cortex_label = op.join(freesurfer_dir,'fsaverage4/label/lh.cortex.label')
    fs4_indexlist_left.inputs.out_file = subject_ID + '_seed_index_fs4_left.txt'
    #fs4_indexlist_left.run_without_submitting = True
    dmripipeline.connect([(index_fsaverage4_left, fs4_indexlist_left, [("out_file", "in_surface_values")])])
    
    fs4_indexlist_right = fs4_indexlist_left.clone(name='82_index_fsav4_right')
    fs4_indexlist_right.inputs.cortex_label = op.join(freesurfer_dir,'fsaverage4/label/rh.cortex.label')
    fs4_indexlist_right.inputs.out_file = subject_ID + '_seed_index_fs4_right.txt'
    dmripipeline.connect([(index_fsaverage4_right, fs4_indexlist_right, [("out_file", "in_surface_values")])])
    
    
    """
    downsample matrices according to fsaverage projections
    """
    if (not use_sample):
        connect_mat_fs4_nat_left_left = pe.Node(interface=Function(input_names=["index_row_file","index_col_file","matrix_file","out_prefix","dist2sim"], output_names=["out_mat","out_nii"], function=downsample_matrix), name='83_connect_mat_fs4_nat_left_left')
        connect_mat_fs4_nat_left_left.inputs.out_prefix = subject_ID + '_connect_fs4_nat_left_left'
        connect_mat_fs4_nat_left_left.inputs.dist2sim = False
        dmripipeline.connect(fs4_indexlist_left, "out_file", connect_mat_fs4_nat_left_left,"index_row_file")
        dmripipeline.connect(fs4_indexlist_left, "out_file", connect_mat_fs4_nat_left_left,"index_col_file")
        dmripipeline.connect(submatrix_left_left, "mat_matrix_nat", connect_mat_fs4_nat_left_left,"matrix_file")
        
        connect_mat_fs4_nat_left_right = connect_mat_fs4_nat_left_left.clone(name='83_connect_mat_fs4_nat_left_right')
        connect_mat_fs4_nat_left_right.inputs.out_prefix = subject_ID + '_connect_fs4_nat_left_right'
        dmripipeline.connect(fs4_indexlist_left, "out_file", connect_mat_fs4_nat_left_right,"index_row_file")
        dmripipeline.connect(fs4_indexlist_right, "out_file", connect_mat_fs4_nat_left_right,"index_col_file")
        dmripipeline.connect(submatrix_left_right, "mat_matrix_nat", connect_mat_fs4_nat_left_right,"matrix_file")
        
        connect_mat_fs4_nat_right_left = connect_mat_fs4_nat_left_left.clone(name='83_connect_mat_fs4_nat_right_left')
        connect_mat_fs4_nat_right_left.inputs.out_prefix = subject_ID + '_connect_fs4_nat_right_left'
        dmripipeline.connect(fs4_indexlist_right, "out_file", connect_mat_fs4_nat_right_left,"index_row_file")
        dmripipeline.connect(fs4_indexlist_left, "out_file", connect_mat_fs4_nat_right_left,"index_col_file")
        dmripipeline.connect(submatrix_right_left, "mat_matrix_nat", connect_mat_fs4_nat_right_left,"matrix_file")
        
        connect_mat_fs4_nat_right_right = connect_mat_fs4_nat_left_left.clone(name='83_connect_mat_fs4_nat_right_right')
        connect_mat_fs4_nat_right_right.inputs.out_prefix = subject_ID + '_connect_fs4_nat_right_right'
        dmripipeline.connect(fs4_indexlist_right, "out_file", connect_mat_fs4_nat_right_right,"index_row_file")
        dmripipeline.connect(fs4_indexlist_right, "out_file", connect_mat_fs4_nat_right_right,"index_col_file")
        dmripipeline.connect(submatrix_right_right, "mat_matrix_nat", connect_mat_fs4_nat_right_right,"matrix_file")
        
        connect_mat_fs4_log_left_left = connect_mat_fs4_nat_left_left.clone(name='83_connect_mat_fs4_log_left_left')
        connect_mat_fs4_log_left_left.inputs.out_prefix = subject_ID + '_connect_fs4_log_left_left'
        dmripipeline.connect(fs4_indexlist_left, "out_file", connect_mat_fs4_log_left_left,"index_row_file")
        dmripipeline.connect(fs4_indexlist_left, "out_file", connect_mat_fs4_log_left_left,"index_col_file")
        dmripipeline.connect(submatrix_left_left, "mat_matrix_log", connect_mat_fs4_log_left_left,"matrix_file")
        
        connect_mat_fs4_log_left_right = connect_mat_fs4_log_left_left.clone(name='83_connect_mat_fs4_log_left_right')
        connect_mat_fs4_log_left_right.inputs.out_prefix = subject_ID + '_connect_fs4_log_left_right'
        dmripipeline.connect(fs4_indexlist_left, "out_file", connect_mat_fs4_log_left_right,"index_row_file")
        dmripipeline.connect(fs4_indexlist_right, "out_file", connect_mat_fs4_log_left_right,"index_col_file")
        dmripipeline.connect(submatrix_left_right, "mat_matrix_log", connect_mat_fs4_log_left_right,"matrix_file")
        
        connect_mat_fs4_log_right_left = connect_mat_fs4_log_left_left.clone(name='83_connect_mat_fs4_log_right_left')
        connect_mat_fs4_log_right_left.inputs.out_prefix = subject_ID + '_connect_fs4_log_right_left'
        dmripipeline.connect(fs4_indexlist_right, "out_file", connect_mat_fs4_log_right_left,"index_row_file")
        dmripipeline.connect(fs4_indexlist_left, "out_file", connect_mat_fs4_log_right_left,"index_col_file")
        dmripipeline.connect(submatrix_right_left, "mat_matrix_log", connect_mat_fs4_log_right_left,"matrix_file")
        
        connect_mat_fs4_log_right_right = connect_mat_fs4_log_left_left.clone(name='83_connect_mat_fs4_log_right_right')
        connect_mat_fs4_log_right_right.inputs.out_prefix = subject_ID + '_connect_fs4_log_right_right'
        dmripipeline.connect(fs4_indexlist_right, "out_file", connect_mat_fs4_log_right_right,"index_row_file")
        dmripipeline.connect(fs4_indexlist_right, "out_file", connect_mat_fs4_log_right_right,"index_col_file")
        dmripipeline.connect(submatrix_right_right, "mat_matrix_log", connect_mat_fs4_log_right_right,"matrix_file")
        
#         connect_mat_fs4_nat_full = pe.Node(interface=Function(input_names=["sm_left_left", "sm_left_right","sm_right_left", "sm_right_right", "out_filename"], output_names=["out_file"], function=merge_matrices), name='83_connect_mat_fs4_nat_full')
#         connect_mat_fs4_nat_full.inputs.out_filename = subject_ID + '_connect_fs4_nat_full.mat'
#         connect_mat_fs4_nat_full.run_without_submitting = True
#         dmripipeline.connect(connect_mat_fs4_nat_left_left, "out_nii", connect_mat_fs4_nat_full, "sm_left_left")
#         dmripipeline.connect(connect_mat_fs4_nat_left_right, "out_nii", connect_mat_fs4_nat_full, "sm_left_right")
#         dmripipeline.connect(connect_mat_fs4_nat_right_left, "out_nii", connect_mat_fs4_nat_full, "sm_right_left")
#         dmripipeline.connect(connect_mat_fs4_nat_right_right, "out_nii", connect_mat_fs4_nat_full, "sm_right_right")
#         
#         connect_mat_fs4_log_full = connect_mat_fs4_nat_full.clone(name='83_connect_mat_fs4_log_full')
#         connect_mat_fs4_log_full.inputs.outfile_prefix = subject_ID + '_connect_fs4_log_full.mat'
#         connect_mat_fs4_log_full.run_without_submitting = True
#         dmripipeline.connect(connect_mat_fs4_log_left_left, "out_nii", connect_mat_fs4_log_full, "sm_left_left")
#         dmripipeline.connect(connect_mat_fs4_log_left_right, "out_nii", connect_mat_fs4_log_full, "sm_left_right")
#         dmripipeline.connect(connect_mat_fs4_log_right_left, "out_nii", connect_mat_fs4_log_full, "sm_right_left")
#         dmripipeline.connect(connect_mat_fs4_log_right_right, "out_nii", connect_mat_fs4_log_full, "sm_right_right")
        


        connect_mat_fs5_nat_left_left = connect_mat_fs4_nat_left_left.clone(name='83_connect_mat_fs5_nat_left_left')
        connect_mat_fs5_nat_left_left.inputs.out_prefix = subject_ID + '_connect_fs5_nat_left_left'
        dmripipeline.connect(fs5_indexlist_left, "out_file", connect_mat_fs5_nat_left_left,"index_row_file")
        dmripipeline.connect(fs5_indexlist_left, "out_file", connect_mat_fs5_nat_left_left,"index_col_file")
        dmripipeline.connect(submatrix_left_left, "mat_matrix_nat", connect_mat_fs5_nat_left_left,"matrix_file")
        
        connect_mat_fs5_nat_left_right = connect_mat_fs5_nat_left_left.clone(name='83_connect_mat_fs5_nat_left_right')
        connect_mat_fs5_nat_left_right.inputs.out_prefix = subject_ID + '_connect_fs5_nat_left_right'
        dmripipeline.connect(fs5_indexlist_left, "out_file", connect_mat_fs5_nat_left_right,"index_row_file")
        dmripipeline.connect(fs5_indexlist_right, "out_file", connect_mat_fs5_nat_left_right,"index_col_file")
        dmripipeline.connect(submatrix_left_right, "mat_matrix_nat", connect_mat_fs5_nat_left_right,"matrix_file")
        
        connect_mat_fs5_nat_right_left = connect_mat_fs5_nat_left_left.clone(name='83_connect_mat_fs5_nat_right_left')
        connect_mat_fs5_nat_right_left.inputs.out_prefix = subject_ID + '_connect_fs5_nat_right_left'
        dmripipeline.connect(fs5_indexlist_right, "out_file", connect_mat_fs5_nat_right_left,"index_row_file")
        dmripipeline.connect(fs5_indexlist_left, "out_file", connect_mat_fs5_nat_right_left,"index_col_file")
        dmripipeline.connect(submatrix_right_left, "mat_matrix_nat", connect_mat_fs5_nat_right_left,"matrix_file")
        
        connect_mat_fs5_nat_right_right = connect_mat_fs5_nat_left_left.clone(name='83_connect_mat_fs5_nat_right_right')
        connect_mat_fs5_nat_right_right.inputs.out_prefix = subject_ID + '_connect_fs5_nat_right_right'
        dmripipeline.connect(fs5_indexlist_right, "out_file", connect_mat_fs5_nat_right_right,"index_row_file")
        dmripipeline.connect(fs5_indexlist_right, "out_file", connect_mat_fs5_nat_right_right,"index_col_file")
        dmripipeline.connect(submatrix_right_right, "mat_matrix_nat", connect_mat_fs5_nat_right_right,"matrix_file")
        
        connect_mat_fs5_log_left_left = connect_mat_fs5_nat_left_left.clone(name='83_connect_mat_fs5_log_left_left')
        connect_mat_fs5_log_left_left.inputs.out_prefix = subject_ID + '_connect_fs5_log_left_left'
        dmripipeline.connect(fs5_indexlist_left, "out_file", connect_mat_fs5_log_left_left,"index_row_file")
        dmripipeline.connect(fs5_indexlist_left, "out_file", connect_mat_fs5_log_left_left,"index_col_file")
        dmripipeline.connect(submatrix_left_left, "mat_matrix_log", connect_mat_fs5_log_left_left,"matrix_file")
        
        connect_mat_fs5_log_left_right = connect_mat_fs5_log_left_left.clone(name='83_connect_mat_fs5_log_left_right')
        connect_mat_fs5_log_left_right.inputs.out_prefix = subject_ID + '_connect_fs5_log_left_right'
        dmripipeline.connect(fs5_indexlist_left, "out_file", connect_mat_fs5_log_left_right,"index_row_file")
        dmripipeline.connect(fs5_indexlist_right, "out_file", connect_mat_fs5_log_left_right,"index_col_file")
        dmripipeline.connect(submatrix_left_right, "mat_matrix_log", connect_mat_fs5_log_left_right,"matrix_file")
        
        connect_mat_fs5_log_right_left = connect_mat_fs5_log_left_left.clone(name='83_connect_mat_fs5_log_right_left')
        connect_mat_fs5_log_right_left.inputs.out_prefix = subject_ID + '_connect_fs5_log_right_left'
        dmripipeline.connect(fs5_indexlist_right, "out_file", connect_mat_fs5_log_right_left,"index_row_file")
        dmripipeline.connect(fs5_indexlist_left, "out_file", connect_mat_fs5_log_right_left,"index_col_file")
        dmripipeline.connect(submatrix_right_left, "mat_matrix_log", connect_mat_fs5_log_right_left,"matrix_file")
        
        connect_mat_fs5_log_right_right = connect_mat_fs5_log_left_left.clone(name='83_connect_mat_fs5_log_right_right')
        connect_mat_fs5_log_right_right.inputs.out_prefix = subject_ID + '_connect_fs5_log_right_right'
        dmripipeline.connect(fs5_indexlist_right, "out_file", connect_mat_fs5_log_right_right,"index_row_file")
        dmripipeline.connect(fs5_indexlist_right, "out_file", connect_mat_fs5_log_right_right,"index_col_file")
        dmripipeline.connect(submatrix_right_right, "mat_matrix_log", connect_mat_fs5_log_right_right,"matrix_file")
        
#         connect_mat_fs5_nat_full = connect_mat_fs4_nat_full.clone(name='83_connect_mat_fs5_nat_full')
#         connect_mat_fs5_nat_full.inputs.outfile_prefix = subject_ID + '_connect_fs5_nat_full.mat'
#         connect_mat_fs5_nat_full.run_without_submitting = True
#         dmripipeline.connect(connect_mat_fs5_nat_left_left, "out_nii", connect_mat_fs5_nat_full, "sm_left_left")
#         dmripipeline.connect(connect_mat_fs5_nat_left_right, "out_nii", connect_mat_fs5_nat_full, "sm_left_right")
#         dmripipeline.connect(connect_mat_fs5_nat_right_left, "out_nii", connect_mat_fs5_nat_full, "sm_right_left")
#         dmripipeline.connect(connect_mat_fs5_nat_right_right, "out_nii", connect_mat_fs5_nat_full, "sm_right_right")
#         
#         connect_mat_fs5_log_full = connect_mat_fs5_nat_full.clone(name='83_connect_mat_fs5_log_full')
#         connect_mat_fs5_log_full.inputs.out_filename = subject_ID + '_connect_fs5_log_full.mat'
#         connect_mat_fs5_log_full.run_without_submitting = True
#         dmripipeline.connect(connect_mat_fs5_log_left_left, "out_nii", connect_mat_fs5_log_full, "sm_left_left")
#         dmripipeline.connect(connect_mat_fs5_log_left_right, "out_nii", connect_mat_fs5_log_full, "sm_left_right")
#         dmripipeline.connect(connect_mat_fs5_log_right_left, "out_nii", connect_mat_fs5_log_full, "sm_right_left")
#         dmripipeline.connect(connect_mat_fs5_log_right_right, "out_nii", connect_mat_fs5_log_full, "sm_right_right")
#         

    """
    use a sink to save outputs
    """
    
    datasink = pe.Node(io.DataSink(), name='99_datasink')
    datasink.inputs.base_directory = output_dir
    datasink.inputs.container = subject_ID
    datasink.inputs.parameterization = True
    #datasink.run_without_submitting = True

    dmripipeline.connect(index_pruned_left, 'out_file', datasink, 'interface_index.@3')
    dmripipeline.connect(index_pruned_right, 'out_file', datasink, 'interface_index.@4')
    dmripipeline.connect(index_final_2_t1_left, 'out_file', datasink, 'interface_index.@5')
    dmripipeline.connect(index_final_2_t1_right, 'out_file', datasink, 'interface_index.@6')
    dmripipeline.connect(index_interface2surf_left, 'out_file', datasink, 'interface_index.@7')
    dmripipeline.connect(index_interface2surf_right, 'out_file', datasink, 'interface_index.@8')
    dmripipeline.connect(index_fsaverage5_left, 'out_file', datasink, 'interface_index.@9')
    dmripipeline.connect(index_fsaverage5_right, 'out_file', datasink, 'interface_index.@10')
    dmripipeline.connect(fs5_indexlist_left, 'out_file', datasink, 'interface_index.@11')
    dmripipeline.connect(fs5_indexlist_right, 'out_file', datasink, 'interface_index.@12') 
    dmripipeline.connect(index_fsaverage4_left, 'out_file', datasink, 'interface_index.@13')
    dmripipeline.connect(index_fsaverage4_right, 'out_file', datasink, 'interface_index.@14')
    dmripipeline.connect(fs4_indexlist_left, 'out_file', datasink, 'interface_index.@15')
    dmripipeline.connect(fs4_indexlist_right, 'out_file', datasink, 'interface_index.@16')
    dmripipeline.connect(fs_indexlist_left, 'out_file', datasink, 'interface_index.@17')
    dmripipeline.connect(fs_indexlist_right, 'out_file', datasink, 'interface_index.@18')
    dmripipeline.connect(tract_exclusion_mask, 'outfile', datasink, 'interface_index.@19')
     
#    dmripipeline.connect(submatrix_left_left, 'mat_matrix_nat', datasink, 'connect_matrix.native.mat')
#    dmripipeline.connect(submatrix_left_left, 'mat_matrix_log', datasink, 'connect_matrix.native.mat.@2')
    dmripipeline.connect(submatrix_left_left, 'nii_matrix_nat', datasink, 'connect_matrix.native.@3')
    dmripipeline.connect(submatrix_left_left, 'nii_matrix_log', datasink, 'connect_matrix.native.@4')
#    dmripipeline.connect(submatrix_right_right, 'mat_matrix_nat', datasink, 'connect_matrix.native.mat.@5')
#    dmripipeline.connect(submatrix_right_right, 'mat_matrix_log', datasink, 'connect_matrix.native.mat.@6')
    dmripipeline.connect(submatrix_right_right, 'nii_matrix_nat', datasink, 'connect_matrix.native.@7')
    dmripipeline.connect(submatrix_right_right, 'nii_matrix_log', datasink, 'connect_matrix.native.@8')
#    dmripipeline.connect(submatrix_left_right, 'mat_matrix_nat', datasink, 'connect_matrix.native.mat')
#    dmripipeline.connect(submatrix_left_right, 'mat_matrix_log', datasink, 'connect_matrix.native.mat.@2')
    dmripipeline.connect(submatrix_left_right, 'nii_matrix_nat', datasink, 'connect_matrix.native.@9')
    dmripipeline.connect(submatrix_left_right, 'nii_matrix_log', datasink, 'connect_matrix.native.@10')
#    dmripipeline.connect(submatrix_right_left, 'mat_matrix_nat', datasink, 'connect_matrix.native.mat')
#    dmripipeline.connect(submatrix_right_left, 'mat_matrix_log', datasink, 'connect_matrix.native.mat.@2')
    dmripipeline.connect(submatrix_right_left, 'nii_matrix_nat', datasink, 'connect_matrix.native.@11')
    dmripipeline.connect(submatrix_right_left, 'nii_matrix_log', datasink, 'connect_matrix.native.@12')
    
#     dmripipeline.connect(full_matrix_nat, 'out_file', datasink, 'connect_matrix.native.@9')
#     dmripipeline.connect(full_matrix_log, 'out_file', datasink, 'connect_matrix.native.@11')

    
    if (not use_sample):
#        dmripipeline.connect(connect_mat_fs4_nat_left_left, 'out_mat', datasink, 'connect_matrix.fs4.mat.@1')
#        dmripipeline.connect(connect_mat_fs4_log_left_left, 'out_mat', datasink, 'connect_matrix.fs4.mat.@2')
#        dmripipeline.connect(connect_mat_fs4_nat_right_right, 'out_mat', datasink, 'connect_matrix.fs4.mat.@3')
#        dmripipeline.connect(connect_mat_fs4_log_right_right, 'out_mat', datasink, 'connect_matrix.fs4.mat.@4')
#        dmripipeline.connect(connect_mat_fs4_nat_left_right, 'out_mat', datasink, 'connect_matrix.fs4.mat.@5')
#        dmripipeline.connect(connect_mat_fs4_log_left_right, 'out_mat', datasink, 'connect_matrix.fs4.mat.@6')
#        dmripipeline.connect(connect_mat_fs4_nat_right_left, 'out_mat', datasink, 'connect_matrix.fs4.mat.@7')
#        dmripipeline.connect(connect_mat_fs4_log_right_left, 'out_mat', datasink, 'connect_matrix.fs4.mat.@8')
        
        dmripipeline.connect(connect_mat_fs4_nat_left_left, 'out_nii', datasink, 'connect_matrix.fs4.@1')
        dmripipeline.connect(connect_mat_fs4_log_left_left, 'out_nii', datasink, 'connect_matrix.fs4.@2')
        dmripipeline.connect(connect_mat_fs4_nat_right_right, 'out_nii', datasink, 'connect_matrix.fs4.@3')
        dmripipeline.connect(connect_mat_fs4_log_right_right, 'out_nii', datasink, 'connect_matrix.fs4.@4')
        dmripipeline.connect(connect_mat_fs4_nat_left_right, 'out_nii', datasink, 'connect_matrix.fs4.@5')
        dmripipeline.connect(connect_mat_fs4_log_left_right, 'out_nii', datasink, 'connect_matrix.fs4.@6')
        dmripipeline.connect(connect_mat_fs4_nat_right_left, 'out_nii', datasink, 'connect_matrix.fs4.@7')
        dmripipeline.connect(connect_mat_fs4_log_right_left, 'out_nii', datasink, 'connect_matrix.fs4.@8')

#         dmripipeline.connect(connect_mat_fs4_nat_full, 'out_file', datasink, 'connect_matrix.@28')
#         dmripipeline.connect(connect_mat_fs4_log_full, 'out_file', datasink, 'connect_matrix.@30')        
        
#        dmripipeline.connect(connect_mat_fs5_nat_left_left, 'out_mat', datasink, 'connect_matrix.fs5.mat.@1')
#        dmripipeline.connect(connect_mat_fs5_log_left_left, 'out_mat', datasink, 'connect_matrix.fs5.mat.@2')
#        dmripipeline.connect(connect_mat_fs5_nat_right_right, 'out_mat', datasink, 'connect_matrix.fs5.mat.@3')
#        dmripipeline.connect(connect_mat_fs5_log_right_right, 'out_mat', datasink, 'connect_matrix.fs5.mat.@4')
#        dmripipeline.connect(connect_mat_fs5_nat_left_right, 'out_mat', datasink, 'connect_matrix.fs5.mat.@5')
#        dmripipeline.connect(connect_mat_fs5_log_left_right, 'out_mat', datasink, 'connect_matrix.fs5.mat.@6')
#        dmripipeline.connect(connect_mat_fs5_nat_right_left, 'out_mat', datasink, 'connect_matrix.fs5.mat.@7')
#        dmripipeline.connect(connect_mat_fs5_log_right_left, 'out_mat', datasink, 'connect_matrix.fs5.mat.@8')
        
        dmripipeline.connect(connect_mat_fs5_nat_left_left, 'out_nii', datasink, 'connect_matrix.fs5.@1')     
        dmripipeline.connect(connect_mat_fs5_log_left_left, 'out_nii', datasink, 'connect_matrix.fs5.@2')
        dmripipeline.connect(connect_mat_fs5_nat_right_right, 'out_nii', datasink, 'connect_matrix.fs5.@3')
        dmripipeline.connect(connect_mat_fs5_log_right_right, 'out_nii', datasink, 'connect_matrix.fs5.@4')
        dmripipeline.connect(connect_mat_fs5_nat_left_right, 'out_nii', datasink, 'connect_matrix.fs5.@5')     
        dmripipeline.connect(connect_mat_fs5_log_left_right, 'out_nii', datasink, 'connect_matrix.fs5.@6')
        dmripipeline.connect(connect_mat_fs5_nat_right_left, 'out_nii', datasink, 'connect_matrix.fs5.@7')
        dmripipeline.connect(connect_mat_fs5_log_right_left, 'out_nii', datasink, 'connect_matrix.fs5.@8')

#         dmripipeline.connect(connect_mat_fs5_nat_full, 'out_file', datasink, 'connect_matrix.@40')
#         dmripipeline.connect(connect_mat_fs5_log_full, 'out_file', datasink, 'connect_matrix.@42')
    
    


    
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
    
    connectprepro = pe.Workflow(name="dmri_pipe3_projection")
    
    connectprepro.base_dir = op.abspath(workflow_dir+ "/workflow_"+subject_ID)
    connectprepro.connect([(datasource, dmripipeline, [('wm', 'inputnode.wm'),('seeds_left', 'inputnode.seeds_left'),('seeds_right', 'inputnode.seeds_right'),
                                                       ('t1', 'inputnode.t1'),('warp', 'inputnode.warp'),('inv_flirt_mat', 'inputnode.inv_flirt_mat'),
                                                       ('fa', 'inputnode.fa'),('index_left', 'inputnode.index_left'),('index_right', 'inputnode.index_right')]),
                           (tracts_left_source, dmripipeline, [('tracts_left', 'inputnode.tracts_left')]),
                           (tracts_right_source, dmripipeline, [('tracts_right', 'inputnode.tracts_right')])])
    
    return connectprepro
