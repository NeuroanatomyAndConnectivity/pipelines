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

def do_pipe6_decimate2pfc(subject_ID, workflow_dir, output_dir):

    """
    Packages and Data Setup
    =======================
    Import necessary modules from nipype.
    """
    
    
    import nipype.interfaces.io as io  # Data i/o
    import nipype.interfaces.utility as util  # utility
    import nipype.pipeline.engine as pe  # pipeline engine
    import os.path as op  # system functions
    from nipype.interfaces.utility import Function
    from dmri_pipe_aux import mask_fs_matrix
    from dmri_pipe_aux import transpose_matrix
    from dmri_pipe_aux import merge_matrices


    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    define the workflow
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    dmripipeline = pe.Workflow(name = 'pipe6_decimate2pfc' )
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Use datasource node to perform the actual data grabbing.
    Templates for the associated images are used to obtain the correct images.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    
    data_template = "%s/%s/%s%s"
    
    info = dict(conmat_fs4_nat_lh = [[subject_ID,'connect_matrix/fs4', subject_ID, '_connect_fs4_nat_left_left.nii']],
                conmat_fs4_nat_rh = [[subject_ID,'connect_matrix/fs4', subject_ID, '_connect_fs4_nat_right_right.nii']],
                conmat_fs4_nat_lr = [[subject_ID,'connect_matrix/fs4', subject_ID, '_connect_fs4_nat_left_right.nii']],
                conmat_fs4_nat_rl = [[subject_ID,'connect_matrix/fs4', subject_ID, '_connect_fs4_nat_right_left.nii']],
                conmat_fs4_log_lh = [[subject_ID,'connect_matrix/fs4', subject_ID, '_connect_fs4_log_left_left.nii']],
                conmat_fs4_log_rh = [[subject_ID,'connect_matrix/fs4', subject_ID, '_connect_fs4_log_right_right.nii']],
                conmat_fs4_log_lr = [[subject_ID,'connect_matrix/fs4', subject_ID, '_connect_fs4_log_left_right.nii']],
                conmat_fs4_log_rl = [[subject_ID,'connect_matrix/fs4', subject_ID, '_connect_fs4_log_right_left.nii']],
                
                conmat_fs5_nat_lh = [[subject_ID,'connect_matrix/fs5', subject_ID, '_connect_fs5_nat_left_left.nii']],
                conmat_fs5_nat_rh = [[subject_ID,'connect_matrix/fs5', subject_ID, '_connect_fs5_nat_right_right.nii']],
                conmat_fs5_nat_lr = [[subject_ID,'connect_matrix/fs5', subject_ID, '_connect_fs5_nat_left_right.nii']],
                conmat_fs5_nat_rl = [[subject_ID,'connect_matrix/fs5', subject_ID, '_connect_fs5_nat_right_left.nii']],
                conmat_fs5_log_lh = [[subject_ID,'connect_matrix/fs5', subject_ID, '_connect_fs5_log_left_left.nii']],
                conmat_fs5_log_rh = [[subject_ID,'connect_matrix/fs5', subject_ID, '_connect_fs5_log_right_right.nii']],
                conmat_fs5_log_lr = [[subject_ID,'connect_matrix/fs5', subject_ID, '_connect_fs5_log_left_right.nii']],
                conmat_fs5_log_rl = [[subject_ID,'connect_matrix/fs5', subject_ID, '_connect_fs5_log_right_left.nii']],
                
                simmat_fs4_nat_lh = [[subject_ID,'similarity_matrix/fs4', subject_ID, '_simmat_fs4_nat_left.nii']],
                simmat_fs4_nat_rh = [[subject_ID,'similarity_matrix/fs4', subject_ID, '_simmat_fs4_nat_right.nii']],
                simmat_fs4_nat_lr = [[subject_ID,'similarity_matrix/fs4', subject_ID, '_simmat_fs4_nat_left_right.nii']],
                simmat_fs4_log_lh = [[subject_ID,'similarity_matrix/fs4', subject_ID, '_simmat_fs4_log_left.nii']],
                simmat_fs4_log_rh = [[subject_ID,'similarity_matrix/fs4', subject_ID, '_simmat_fs4_log_right.nii']],
                simmat_fs4_log_lr = [[subject_ID,'similarity_matrix/fs4', subject_ID, '_simmat_fs4_log_left_right.nii']],
                
                simmat_fs5_nat_lh = [[subject_ID,'similarity_matrix/fs5', subject_ID, '_simmat_fs5_nat_left.nii']],
                simmat_fs5_nat_rh = [[subject_ID,'similarity_matrix/fs5', subject_ID, '_simmat_fs5_nat_right.nii']],
                simmat_fs5_nat_lr = [[subject_ID,'similarity_matrix/fs5', subject_ID, '_simmat_fs5_nat_left_right.nii']],
                simmat_fs5_log_lh = [[subject_ID,'similarity_matrix/fs5', subject_ID, '_simmat_fs5_log_left.nii']],
                simmat_fs5_log_rh = [[subject_ID,'similarity_matrix/fs5', subject_ID, '_simmat_fs5_log_right.nii']],
                simmat_fs5_log_lr = [[subject_ID,'similarity_matrix/fs5', subject_ID, '_simmat_fs5_log_left_right.nii']],

                pfc_mask_fs4_lh = [['clustering_results','indices', 'targetmask_fs4_lh.nii','']],
                pfc_mask_fs4_rh = [['clustering_results','indices', 'targetmask_fs4_rh.nii','']],
                pfc_mask_fs5_lh = [['clustering_results','indices', 'targetmask_fs5_lh.nii','']],
                pfc_mask_fs5_rh = [['clustering_results','indices', 'targetmask_fs5_rh.nii','']]
                )
    
    
    datasource = pe.Node(interface=io.DataGrabber(outfields=info.keys()), name='datasource')
    datasource.inputs.template = data_template
    datasource.inputs.base_directory = output_dir
    datasource.inputs.template_args = info
    datasource.inputs.sort_filelist = True
    datasource.run_without_submitting = True
    
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    The input node declared here will be the main
    conduits for the raw data to the rest of the processing pipeline.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    inputnode = pe.Node(interface=util.IdentityInterface(fields=["conmat_fs4_nat_lh", "conmat_fs4_nat_rh", "conmat_fs4_nat_lr", "conmat_fs4_nat_rl", "conmat_fs4_log_lh", "conmat_fs4_log_rh", "conmat_fs4_log_lr", "conmat_fs4_log_rl",
                                                                 "conmat_fs5_nat_lh", "conmat_fs5_nat_rh", "conmat_fs5_nat_lr", "conmat_fs5_nat_rl", "conmat_fs5_log_lh", "conmat_fs5_log_rh", "conmat_fs5_log_lr", "conmat_fs5_log_rl",
                                                                 "simmat_fs4_nat_lh", "simmat_fs4_nat_rh", "simmat_fs4_nat_lr",                      "simmat_fs4_log_lh", "simmat_fs4_log_rh", "simmat_fs4_log_lr",
                                                                 "simmat_fs5_nat_lh", "simmat_fs5_nat_rh", "simmat_fs5_nat_lr",                      "simmat_fs5_log_lh", "simmat_fs5_log_rh", "simmat_fs5_log_lr",
                                                                 "pfc_mask_fs4_lh", "pfc_mask_fs4_rh", "pfc_mask_fs5_lh", "pfc_mask_fs5_rh"]), name="inputnode")
    
    """
    conmat fs4: convert full hemisphere fsaverage to pfc_masked matrices
    """
   
    pfc_conmat_fs4_nat_lh = pe.Node(interface=Function(input_names=["in_matrix_nii","mask_row_nii","mask_col_nii","out_matrix_nii"], output_names=["masked_matrix"], function=mask_fs_matrix), name='80_pfc_conmat_fs4_nat_lh')
    pfc_conmat_fs4_nat_lh.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs4_nat_lh.nii"
    dmripipeline.connect(inputnode, "conmat_fs4_nat_lh", pfc_conmat_fs4_nat_lh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_conmat_fs4_nat_lh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_conmat_fs4_nat_lh,"mask_col_nii")
    
    
    pfc_conmat_fs4_nat_rh = pfc_conmat_fs4_nat_lh.clone(name='80_pfc_conmat_fs4_nat_rh')
    pfc_conmat_fs4_nat_rh.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs4_nat_rh.nii"
    dmripipeline.connect(inputnode, "conmat_fs4_nat_rh", pfc_conmat_fs4_nat_rh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_conmat_fs4_nat_rh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_conmat_fs4_nat_rh,"mask_col_nii")
    
    pfc_conmat_fs4_nat_lr = pfc_conmat_fs4_nat_lh.clone(name='80_pfc_conmat_fs4_nat_lr')
    pfc_conmat_fs4_nat_lr.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs4_nat_lr.nii"
    dmripipeline.connect(inputnode, "conmat_fs4_nat_lr", pfc_conmat_fs4_nat_lr,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_conmat_fs4_nat_lr,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_conmat_fs4_nat_lr,"mask_col_nii")
    
    pfc_conmat_fs4_nat_rl = pfc_conmat_fs4_nat_lh.clone(name='80_pfc_conmat_fs4_nat_rl')
    pfc_conmat_fs4_nat_rl.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs4_nat_rl.nii"
    dmripipeline.connect(inputnode, "conmat_fs4_nat_rl", pfc_conmat_fs4_nat_rl,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_conmat_fs4_nat_rl,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_conmat_fs4_nat_rl,"mask_col_nii")
    
    
    pfc_conmat_fs4_log_lh = pfc_conmat_fs4_nat_lh.clone(name='80_pfc_conmat_fs4_log_lh')
    pfc_conmat_fs4_log_lh.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs4_log_lh.nii"
    dmripipeline.connect(inputnode, "conmat_fs4_log_lh", pfc_conmat_fs4_log_lh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_conmat_fs4_log_lh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_conmat_fs4_log_lh,"mask_col_nii")
    
    
    pfc_conmat_fs4_log_rh = pfc_conmat_fs4_nat_lh.clone(name='80_pfc_conmat_fs4_log_rh')
    pfc_conmat_fs4_log_rh.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs4_log_rh.nii"
    dmripipeline.connect(inputnode, "conmat_fs4_log_rh", pfc_conmat_fs4_log_rh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_conmat_fs4_log_rh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_conmat_fs4_log_rh,"mask_col_nii")
    
    pfc_conmat_fs4_log_lr = pfc_conmat_fs4_nat_lh.clone(name='80_pfc_conmat_fs4_log_lr')
    pfc_conmat_fs4_log_lr.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs4_log_lr.nii"
    dmripipeline.connect(inputnode, "conmat_fs4_log_lr", pfc_conmat_fs4_log_lr,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_conmat_fs4_log_lr,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_conmat_fs4_log_lr,"mask_col_nii")
    
    pfc_conmat_fs4_log_rl = pfc_conmat_fs4_nat_lh.clone(name='80_pfc_conmat_fs4_log_rl')
    pfc_conmat_fs4_log_rl.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs4_log_rl.nii"
    dmripipeline.connect(inputnode, "conmat_fs4_log_rl", pfc_conmat_fs4_log_rl,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_conmat_fs4_log_rl,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_conmat_fs4_log_rl,"mask_col_nii")
    
    
    """
    conmat fs5: convert full hemisphere fsaverage to pfc_masked matrices
    """
   
    pfc_conmat_fs5_nat_lh = pe.Node(interface=Function(input_names=["in_matrix_nii","mask_row_nii","mask_col_nii","out_matrix_nii"], output_names=["masked_matrix"], function=mask_fs_matrix), name='80_pfc_conmat_fs5_nat_lh')
    pfc_conmat_fs5_nat_lh.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs5_nat_lh.nii"
    dmripipeline.connect(inputnode, "conmat_fs5_nat_lh", pfc_conmat_fs5_nat_lh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_conmat_fs5_nat_lh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_conmat_fs5_nat_lh,"mask_col_nii")
    
    
    pfc_conmat_fs5_nat_rh = pfc_conmat_fs5_nat_lh.clone(name='80_pfc_conmat_fs5_nat_rh')
    pfc_conmat_fs5_nat_rh.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs5_nat_rh.nii"
    dmripipeline.connect(inputnode, "conmat_fs5_nat_rh", pfc_conmat_fs5_nat_rh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_conmat_fs5_nat_rh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_conmat_fs5_nat_rh,"mask_col_nii")
    
    pfc_conmat_fs5_nat_lr = pfc_conmat_fs5_nat_lh.clone(name='80_pfc_conmat_fs5_nat_lr')
    pfc_conmat_fs5_nat_lr.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs5_nat_lr.nii"
    dmripipeline.connect(inputnode, "conmat_fs5_nat_lr", pfc_conmat_fs5_nat_lr,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_conmat_fs5_nat_lr,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_conmat_fs5_nat_lr,"mask_col_nii")
    
    pfc_conmat_fs5_nat_rl = pfc_conmat_fs5_nat_lh.clone(name='80_pfc_conmat_fs5_nat_rl')
    pfc_conmat_fs5_nat_rl.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs5_nat_rl.nii"
    dmripipeline.connect(inputnode, "conmat_fs5_nat_rl", pfc_conmat_fs5_nat_rl,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_conmat_fs5_nat_rl,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_conmat_fs5_nat_rl,"mask_col_nii")
    
    
    pfc_conmat_fs5_log_lh = pfc_conmat_fs5_nat_lh.clone(name='80_pfc_conmat_fs5_log_lh')
    pfc_conmat_fs5_log_lh.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs5_log_lh.nii"
    dmripipeline.connect(inputnode, "conmat_fs5_log_lh", pfc_conmat_fs5_log_lh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_conmat_fs5_log_lh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_conmat_fs5_log_lh,"mask_col_nii")
    
    
    pfc_conmat_fs5_log_rh = pfc_conmat_fs5_nat_lh.clone(name='80_pfc_conmat_fs5_log_rh')
    pfc_conmat_fs5_log_rh.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs5_log_rh.nii"
    dmripipeline.connect(inputnode, "conmat_fs5_log_rh", pfc_conmat_fs5_log_rh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_conmat_fs5_log_rh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_conmat_fs5_log_rh,"mask_col_nii")
    
    pfc_conmat_fs5_log_lr = pfc_conmat_fs5_nat_lh.clone(name='80_pfc_conmat_fs5_log_lr')
    pfc_conmat_fs5_log_lr.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs5_log_lr.nii"
    dmripipeline.connect(inputnode, "conmat_fs5_log_lr", pfc_conmat_fs5_log_lr,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_conmat_fs5_log_lr,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_conmat_fs5_log_lr,"mask_col_nii")
    
    pfc_conmat_fs5_log_rl = pfc_conmat_fs5_nat_lh.clone(name='80_pfc_conmat_fs5_log_rl')
    pfc_conmat_fs5_log_rl.inputs.out_matrix_nii = subject_ID + "_pfc_conmat_fs5_log_rl.nii"
    dmripipeline.connect(inputnode, "conmat_fs5_log_rl", pfc_conmat_fs5_log_rl,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_conmat_fs5_log_rl,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_conmat_fs5_log_rl,"mask_col_nii") 
    
    
    
    """
    simmat fs4: convert full hemisphere fsaverage to pfc_masked matrices
    """
   
    pfc_simmat_fs4_nat_lh = pe.Node(interface=Function(input_names=["in_matrix_nii","mask_row_nii","mask_col_nii","out_matrix_nii"], output_names=["masked_matrix"], function=mask_fs_matrix), name='80_pfc_simmat_fs4_nat_lh')
    pfc_simmat_fs4_nat_lh.inputs.out_matrix_nii = subject_ID + "_pfc_simmat_fs4_nat_lh.nii"
    dmripipeline.connect(inputnode, "simmat_fs4_nat_lh", pfc_simmat_fs4_nat_lh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_simmat_fs4_nat_lh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_simmat_fs4_nat_lh,"mask_col_nii")
    
    
    pfc_simmat_fs4_nat_rh = pfc_simmat_fs4_nat_lh.clone(name='80_pfc_simmat_fs4_nat_rh')
    pfc_simmat_fs4_nat_rh.inputs.out_matrix_nii = subject_ID + "_pfc_simmat_fs4_nat_rh.nii"
    dmripipeline.connect(inputnode, "simmat_fs4_nat_rh", pfc_simmat_fs4_nat_rh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_simmat_fs4_nat_rh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_simmat_fs4_nat_rh,"mask_col_nii")
    
    pfc_simmat_fs4_nat_lr = pfc_simmat_fs4_nat_lh.clone(name='80_pfc_simmat_fs4_nat_lr')
    pfc_simmat_fs4_nat_lr.inputs.out_matrix_nii = subject_ID + "_pfc_simmat_fs4_nat_lr.nii"
    dmripipeline.connect(inputnode, "simmat_fs4_nat_lr", pfc_simmat_fs4_nat_lr,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_simmat_fs4_nat_lr,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_simmat_fs4_nat_lr,"mask_col_nii")
    
    
    pfc_simmat_fs4_log_lh = pfc_simmat_fs4_nat_lh.clone(name='80_pfc_simmat_fs4_log_lh')
    pfc_simmat_fs4_log_lh.inputs.out_matrix_nii = subject_ID + "_pfc_simmat_fs4_log_lh.nii"
    dmripipeline.connect(inputnode, "simmat_fs4_log_lh", pfc_simmat_fs4_log_lh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_simmat_fs4_log_lh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_simmat_fs4_log_lh,"mask_col_nii")
    
    
    pfc_simmat_fs4_log_rh = pfc_simmat_fs4_nat_lh.clone(name='80_pfc_simmat_fs4_log_rh')
    pfc_simmat_fs4_log_rh.inputs.out_matrix_nii = subject_ID + "_pfc_simmat_fs4_log_rh.nii"
    dmripipeline.connect(inputnode, "simmat_fs4_log_rh", pfc_simmat_fs4_log_rh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_simmat_fs4_log_rh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_simmat_fs4_log_rh,"mask_col_nii")
    
    pfc_simmat_fs4_log_lr = pfc_simmat_fs4_nat_lh.clone(name='80_pfc_simmat_fs4_log_lr')
    pfc_simmat_fs4_log_lr.inputs.out_matrix_nii = subject_ID + "_pfc_simmat_fs4_log_lr.nii"
    dmripipeline.connect(inputnode, "simmat_fs4_log_lr", pfc_simmat_fs4_log_lr,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_lh", pfc_simmat_fs4_log_lr,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs4_rh", pfc_simmat_fs4_log_lr,"mask_col_nii")
    

    
    
    """
    simmat fs5: convert full hemisphere fsaverage to pfc_masked matrices
    """
   
    pfc_simmat_fs5_nat_lh = pe.Node(interface=Function(input_names=["in_matrix_nii","mask_row_nii","mask_col_nii","out_matrix_nii"], output_names=["masked_matrix"], function=mask_fs_matrix), name='80_pfc_simmat_fs5_nat_lh')
    pfc_simmat_fs5_nat_lh.inputs.out_matrix_nii = subject_ID + "_pfc_simmat_fs5_nat_lh.nii"
    dmripipeline.connect(inputnode, "simmat_fs5_nat_lh", pfc_simmat_fs5_nat_lh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_simmat_fs5_nat_lh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_simmat_fs5_nat_lh,"mask_col_nii")
    
    
    pfc_simmat_fs5_nat_rh = pfc_simmat_fs5_nat_lh.clone(name='80_pfc_simmat_fs5_nat_rh')
    pfc_simmat_fs5_nat_rh.inputs.out_matrix_nii = subject_ID + "_pfc_simmat_fs5_nat_rh.nii"
    dmripipeline.connect(inputnode, "simmat_fs5_nat_rh", pfc_simmat_fs5_nat_rh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_simmat_fs5_nat_rh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_simmat_fs5_nat_rh,"mask_col_nii")
    
    pfc_simmat_fs5_nat_lr = pfc_simmat_fs5_nat_lh.clone(name='80_pfc_simmat_fs5_nat_lr')
    pfc_simmat_fs5_nat_lr.inputs.out_matrix_nii = subject_ID + "_pfc_simmat_fs5_nat_lr.nii"
    dmripipeline.connect(inputnode, "simmat_fs5_nat_lr", pfc_simmat_fs5_nat_lr,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_simmat_fs5_nat_lr,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_simmat_fs5_nat_lr,"mask_col_nii")

    
    
    pfc_simmat_fs5_log_lh = pfc_simmat_fs5_nat_lh.clone(name='80_pfc_simmat_fs5_log_lh')
    pfc_simmat_fs5_log_lh.inputs.out_matrix_nii = subject_ID + "_pfc_simmat_fs5_log_lh.nii"
    dmripipeline.connect(inputnode, "simmat_fs5_log_lh", pfc_simmat_fs5_log_lh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_simmat_fs5_log_lh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_simmat_fs5_log_lh,"mask_col_nii")
    
    
    pfc_simmat_fs5_log_rh = pfc_simmat_fs5_nat_lh.clone(name='80_pfc_simmat_fs5_log_rh')
    pfc_simmat_fs5_log_rh.inputs.out_matrix_nii = subject_ID + "_pfc_simmat_fs5_log_rh.nii"
    dmripipeline.connect(inputnode, "simmat_fs5_log_rh", pfc_simmat_fs5_log_rh,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_simmat_fs5_log_rh,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_simmat_fs5_log_rh,"mask_col_nii")
    
    pfc_simmat_fs5_log_lr = pfc_simmat_fs5_nat_lh.clone(name='80_pfc_simmat_fs5_log_lr')
    pfc_simmat_fs5_log_lr.inputs.out_matrix_nii = subject_ID + "_pfc_simmat_fs5_log_lr.nii"
    dmripipeline.connect(inputnode, "simmat_fs5_log_lr", pfc_simmat_fs5_log_lr,"in_matrix_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_lh", pfc_simmat_fs5_log_lr,"mask_row_nii")
    dmripipeline.connect(inputnode, "pfc_mask_fs5_rh", pfc_simmat_fs5_log_lr,"mask_col_nii")
    
    
    """
    simmat rl is obtained as transposed lr
    """
    
    pfc_simmat_fs4_nat_rl = pe.Node(interface=Function(input_names=["in_matrix","out_filename"], output_names=["out_file"], function=transpose_matrix), name='80_pfc_simmat_fs4_nat_rl')
    pfc_simmat_fs4_nat_rl.inputs.out_filename = subject_ID + "_pfc_simmat_fs4_nat_rl.nii"
    dmripipeline.connect(pfc_simmat_fs4_nat_lr, "masked_matrix", pfc_simmat_fs4_nat_rl,"in_matrix")
    
    pfc_simmat_fs4_log_rl = pfc_simmat_fs4_nat_rl.clone(name='80_pfc_simmat_fs4_log_rl')
    pfc_simmat_fs4_log_rl.inputs.out_filename = subject_ID + "_pfc_simmat_fs4_log_rl.nii"
    dmripipeline.connect(pfc_simmat_fs4_log_lr, "masked_matrix", pfc_simmat_fs4_log_rl,"in_matrix")
    
    
    pfc_simmat_fs5_nat_rl = pfc_simmat_fs4_nat_rl.clone(name='80_pfc_simmat_fs5_nat_rl')
    pfc_simmat_fs5_nat_rl.inputs.out_filename = subject_ID + "_pfc_simmat_fs5_nat_rl.nii"
    dmripipeline.connect(pfc_simmat_fs5_nat_lr, "masked_matrix", pfc_simmat_fs5_nat_rl,"in_matrix")
    
    pfc_simmat_fs5_log_rl = pfc_simmat_fs4_nat_rl.clone(name='80_pfc_simmat_fs5_log_rl')
    pfc_simmat_fs5_log_rl.inputs.out_filename = subject_ID + "_pfc_simmat_fs5_log_rl.nii"
    dmripipeline.connect(pfc_simmat_fs5_log_lr, "masked_matrix", pfc_simmat_fs5_log_rl,"in_matrix")
    
    
    """
    compute full matrix having info from both hemispheres
    """
    
    pfc_conmat_fs4_nat_full = pe.Node(interface=Function(input_names=["sm_left_left", "sm_left_right","sm_right_left", "sm_right_right", "out_filename","save_as_nii"], output_names=["out_file"], function=merge_matrices), name='85_pfc_conmat_fs4_nat_full')
    pfc_conmat_fs4_nat_full.inputs.out_filename = subject_ID + '_pfc_conmat_fs4_nat_full.nii'
    pfc_conmat_fs4_nat_full.inputs.save_as_nii = True
    pfc_conmat_fs4_nat_full.run_without_submitting = True
    dmripipeline.connect(pfc_conmat_fs4_nat_lh, "masked_matrix", pfc_conmat_fs4_nat_full, "sm_left_left")
    dmripipeline.connect(pfc_conmat_fs4_nat_lr, "masked_matrix", pfc_conmat_fs4_nat_full, "sm_left_right")
    dmripipeline.connect(pfc_conmat_fs4_nat_rl, "masked_matrix", pfc_conmat_fs4_nat_full, "sm_right_left")
    dmripipeline.connect(pfc_conmat_fs4_nat_rh, "masked_matrix", pfc_conmat_fs4_nat_full, "sm_right_right")
    
    pfc_conmat_fs4_log_full = pfc_conmat_fs4_nat_full.clone(name='85_pfc_conmat_fs4_log_full')
    pfc_conmat_fs4_log_full.inputs.out_filename = subject_ID + '_pfc_conmat_fs4_log_full.nii'
    dmripipeline.connect(pfc_conmat_fs4_log_lh, "masked_matrix", pfc_conmat_fs4_log_full, "sm_left_left")
    dmripipeline.connect(pfc_conmat_fs4_log_lr, "masked_matrix", pfc_conmat_fs4_log_full, "sm_left_right")
    dmripipeline.connect(pfc_conmat_fs4_log_rl, "masked_matrix", pfc_conmat_fs4_log_full, "sm_right_left")
    dmripipeline.connect(pfc_conmat_fs4_log_rh, "masked_matrix", pfc_conmat_fs4_log_full, "sm_right_right")
    
    pfc_conmat_fs5_nat_full = pfc_conmat_fs4_nat_full.clone(name='85_pfc_conmat_fs5_nat_full')
    pfc_conmat_fs5_nat_full.inputs.out_filename = subject_ID + '_pfc_conmat_fs5_nat_full.nii'
    dmripipeline.connect(pfc_conmat_fs5_nat_lh, "masked_matrix", pfc_conmat_fs5_nat_full, "sm_left_left")
    dmripipeline.connect(pfc_conmat_fs5_nat_lr, "masked_matrix", pfc_conmat_fs5_nat_full, "sm_left_right")
    dmripipeline.connect(pfc_conmat_fs5_nat_rl, "masked_matrix", pfc_conmat_fs5_nat_full, "sm_right_left")
    dmripipeline.connect(pfc_conmat_fs5_nat_rh, "masked_matrix", pfc_conmat_fs5_nat_full, "sm_right_right")
    
    pfc_conmat_fs5_log_full = pfc_conmat_fs4_nat_full.clone(name='85_pfc_conmat_fs5_log_full')
    pfc_conmat_fs5_log_full.inputs.out_filename = subject_ID + '_pfc_conmat_fs5_log_full.nii'
    dmripipeline.connect(pfc_conmat_fs5_log_lh, "masked_matrix", pfc_conmat_fs5_log_full, "sm_left_left")
    dmripipeline.connect(pfc_conmat_fs5_log_lr, "masked_matrix", pfc_conmat_fs5_log_full, "sm_left_right")
    dmripipeline.connect(pfc_conmat_fs5_log_rl, "masked_matrix", pfc_conmat_fs5_log_full, "sm_right_left")
    dmripipeline.connect(pfc_conmat_fs5_log_rh, "masked_matrix", pfc_conmat_fs5_log_full, "sm_right_right")
    
    
    pfc_simmat_fs4_nat_full = pe.Node(interface=Function(input_names=["sm_left_left", "sm_left_right","sm_right_left", "sm_right_right", "out_filename","save_as_nii"], output_names=["out_file"], function=merge_matrices), name='85_pfc_simmat_fs4_nat_full')
    pfc_simmat_fs4_nat_full.inputs.out_filename = subject_ID + '_pfc_simmat_fs4_nat_full.nii'
    pfc_simmat_fs4_nat_full.inputs.save_as_nii = True
    pfc_simmat_fs4_nat_full.run_without_submitting = True
    dmripipeline.connect(pfc_simmat_fs4_nat_lh, "masked_matrix", pfc_simmat_fs4_nat_full, "sm_left_left")
    dmripipeline.connect(pfc_simmat_fs4_nat_lr, "masked_matrix", pfc_simmat_fs4_nat_full, "sm_left_right")
    dmripipeline.connect(pfc_simmat_fs4_nat_rl, "out_file", pfc_simmat_fs4_nat_full, "sm_right_left")
    dmripipeline.connect(pfc_simmat_fs4_nat_rh, "masked_matrix", pfc_simmat_fs4_nat_full, "sm_right_right")
    
    pfc_simmat_fs4_log_full = pfc_simmat_fs4_nat_full.clone(name='85_pfc_simmat_fs4_log_full')
    pfc_simmat_fs4_log_full.inputs.out_filename = subject_ID + '_pfc_simmat_fs4_log_full.nii'
    dmripipeline.connect(pfc_simmat_fs4_log_lh, "masked_matrix", pfc_simmat_fs4_log_full, "sm_left_left")
    dmripipeline.connect(pfc_simmat_fs4_log_lr, "masked_matrix", pfc_simmat_fs4_log_full, "sm_left_right")
    dmripipeline.connect(pfc_simmat_fs4_log_rl, "out_file", pfc_simmat_fs4_log_full, "sm_right_left")
    dmripipeline.connect(pfc_simmat_fs4_log_rh, "masked_matrix", pfc_simmat_fs4_log_full, "sm_right_right")
    
    pfc_simmat_fs5_nat_full = pfc_simmat_fs4_nat_full.clone(name='85_pfc_simmat_fs5_nat_full')
    pfc_simmat_fs5_nat_full.inputs.out_filename = subject_ID + '_pfc_simmat_fs5_nat_full.nii'
    dmripipeline.connect(pfc_simmat_fs5_nat_lh, "masked_matrix", pfc_simmat_fs5_nat_full, "sm_left_left")
    dmripipeline.connect(pfc_simmat_fs5_nat_lr, "masked_matrix", pfc_simmat_fs5_nat_full, "sm_left_right")
    dmripipeline.connect(pfc_simmat_fs5_nat_rl, "out_file", pfc_simmat_fs5_nat_full, "sm_right_left")
    dmripipeline.connect(pfc_simmat_fs5_nat_rh, "masked_matrix", pfc_simmat_fs5_nat_full, "sm_right_right")
    
    pfc_simmat_fs5_log_full = pfc_simmat_fs4_nat_full.clone(name='85_pfc_simmat_fs5_log_full')
    pfc_simmat_fs5_log_full.inputs.out_filename = subject_ID + '_pfc_simmat_fs5_log_full.nii'
    dmripipeline.connect(pfc_simmat_fs5_log_lh, "masked_matrix", pfc_simmat_fs5_log_full, "sm_left_left")
    dmripipeline.connect(pfc_simmat_fs5_log_lr, "masked_matrix", pfc_simmat_fs5_log_full, "sm_left_right")
    dmripipeline.connect(pfc_simmat_fs5_log_rl, "out_file", pfc_simmat_fs5_log_full, "sm_right_left")
    dmripipeline.connect(pfc_simmat_fs5_log_rh, "masked_matrix", pfc_simmat_fs5_log_full, "sm_right_right")
    
    
    """
    use a sink to save outputs
    """
    
    datasink = pe.Node(io.DataSink(), name='99_datasink')
    datasink.inputs.base_directory = output_dir
    datasink.inputs.container = subject_ID
    datasink.inputs.parameterization = True
    #datasink.run_without_submitting = True

    
    dmripipeline.connect(pfc_conmat_fs4_nat_lh,  'masked_matrix', datasink, 'pfc_matrix.fs4.@1')
    dmripipeline.connect(pfc_conmat_fs4_nat_rh,  'masked_matrix', datasink, 'pfc_matrix.fs4.@2')
    dmripipeline.connect(pfc_conmat_fs4_nat_full,'out_file',      datasink, 'pfc_matrix.fs4.@3')
    dmripipeline.connect(pfc_conmat_fs4_log_lh,  'masked_matrix', datasink, 'pfc_matrix.fs4.@4')
    dmripipeline.connect(pfc_conmat_fs4_log_rh,  'masked_matrix', datasink, 'pfc_matrix.fs4.@5')
    dmripipeline.connect(pfc_conmat_fs4_log_full,'out_file',      datasink, 'pfc_matrix.fs4.@6')
    dmripipeline.connect(pfc_conmat_fs5_nat_lh,  'masked_matrix', datasink, 'pfc_matrix.fs5.@1')
    dmripipeline.connect(pfc_conmat_fs5_nat_rh,  'masked_matrix', datasink, 'pfc_matrix.fs5.@2')
    dmripipeline.connect(pfc_conmat_fs5_nat_full,'out_file',      datasink, 'pfc_matrix.fs5.@3')
    dmripipeline.connect(pfc_conmat_fs5_log_lh,  'masked_matrix', datasink, 'pfc_matrix.fs5.@4')
    dmripipeline.connect(pfc_conmat_fs5_log_rh,  'masked_matrix', datasink, 'pfc_matrix.fs5.@5')
    dmripipeline.connect(pfc_conmat_fs5_log_full,'out_file',      datasink, 'pfc_matrix.fs5.@6')
    
    dmripipeline.connect(pfc_simmat_fs4_nat_lh,  'masked_matrix', datasink, 'pfc_matrix.fs4.@7')
    dmripipeline.connect(pfc_simmat_fs4_nat_rh,  'masked_matrix', datasink, 'pfc_matrix.fs4.@8')
    dmripipeline.connect(pfc_simmat_fs4_nat_full,'out_file',      datasink, 'pfc_matrix.fs4.@9')
    dmripipeline.connect(pfc_simmat_fs4_log_lh,  'masked_matrix', datasink, 'pfc_matrix.fs4.@10')
    dmripipeline.connect(pfc_simmat_fs4_log_rh,  'masked_matrix', datasink, 'pfc_matrix.fs4.@11')
    dmripipeline.connect(pfc_simmat_fs4_log_full,'out_file',      datasink, 'pfc_matrix.fs4.@12')
    dmripipeline.connect(pfc_simmat_fs5_nat_lh,  'masked_matrix', datasink, 'pfc_matrix.fs5.@7')
    dmripipeline.connect(pfc_simmat_fs5_nat_rh,  'masked_matrix', datasink, 'pfc_matrix.fs5.@8')
    dmripipeline.connect(pfc_simmat_fs5_nat_full,'out_file',      datasink, 'pfc_matrix.fs5.@9')
    dmripipeline.connect(pfc_simmat_fs5_log_lh,  'masked_matrix', datasink, 'pfc_matrix.fs5.@10')
    dmripipeline.connect(pfc_simmat_fs5_log_rh,  'masked_matrix', datasink, 'pfc_matrix.fs5.@11')
    dmripipeline.connect(pfc_simmat_fs5_log_full,'out_file',      datasink, 'pfc_matrix.fs5.@12')
    
    
    
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
    
    connectprepro = pe.Workflow(name="dmri_pipe6_decimate2pfc")
    
    connectprepro.base_dir = op.abspath(workflow_dir+ "/workflow_"+subject_ID)
    connectprepro.connect([(datasource, dmripipeline, [("conmat_fs4_nat_lh","inputnode.conmat_fs4_nat_lh"),("conmat_fs4_nat_rh","inputnode.conmat_fs4_nat_rh"),("conmat_fs4_nat_lr","inputnode.conmat_fs4_nat_lr"),("conmat_fs4_nat_rl","inputnode.conmat_fs4_nat_rl"),("conmat_fs4_log_lh","inputnode.conmat_fs4_log_lh"),("conmat_fs4_log_rh","inputnode.conmat_fs4_log_rh"),("conmat_fs4_log_lr","inputnode.conmat_fs4_log_lr"),("conmat_fs4_log_rl","inputnode.conmat_fs4_log_rl"),
                                                       ("conmat_fs5_nat_lh","inputnode.conmat_fs5_nat_lh"),("conmat_fs5_nat_rh","inputnode.conmat_fs5_nat_rh"),("conmat_fs5_nat_lr","inputnode.conmat_fs5_nat_lr"),("conmat_fs5_nat_rl","inputnode.conmat_fs5_nat_rl"),("conmat_fs5_log_lh","inputnode.conmat_fs5_log_lh"),("conmat_fs5_log_rh","inputnode.conmat_fs5_log_rh"),("conmat_fs5_log_lr","inputnode.conmat_fs5_log_lr"),("conmat_fs5_log_rl","inputnode.conmat_fs5_log_rl"),
                                                       ("simmat_fs4_nat_lh","inputnode.simmat_fs4_nat_lh"),("simmat_fs4_nat_rh","inputnode.simmat_fs4_nat_rh"),("simmat_fs4_nat_lr","inputnode.simmat_fs4_nat_lr"),                                                    ("simmat_fs4_log_lh","inputnode.simmat_fs4_log_lh"),("simmat_fs4_log_rh","inputnode.simmat_fs4_log_rh"),("simmat_fs4_log_lr","inputnode.simmat_fs4_log_lr"),
                                                       ("simmat_fs5_nat_lh","inputnode.simmat_fs5_nat_lh"),("simmat_fs5_nat_rh","inputnode.simmat_fs5_nat_rh"),("simmat_fs5_nat_lr","inputnode.simmat_fs5_nat_lr"),                                                    ("simmat_fs5_log_lh","inputnode.simmat_fs5_log_lh"),("simmat_fs5_log_rh","inputnode.simmat_fs5_log_rh"),("simmat_fs5_log_lr","inputnode.simmat_fs5_log_lr"),
                                                       ("pfc_mask_fs4_lh","inputnode.pfc_mask_fs4_lh"),("pfc_mask_fs4_rh","inputnode.pfc_mask_fs4_rh"),("pfc_mask_fs5_lh","inputnode.pfc_mask_fs5_lh"),("pfc_mask_fs5_rh","inputnode.pfc_mask_fs5_rh")])])
    
    return connectprepro
