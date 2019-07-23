'''
Created on Oct 17, 2013

@author: moreno
'''


def do_pipe5_distmat_lr(subject_ID, workflow_dir, output_dir, tract_number, use_sample=False):

    
    """
    Packages and Data Setup
    =======================
    Import necessary modules from nipype.
    """
    
    
    import nipype.interfaces.io as io  # Data i/o
    import nipype.interfaces.utility as util  # utility
    import nipype.pipeline.engine as pe  # pipeline engine
    import nipype.interfaces.fsl as fsl
    import nipype.interfaces.vista as vista
    import os.path as op  # system functions
    import numpy as np
       
    from nipype.interfaces.utility import Function
    from my_custom_interfaces import DistMatrixLat
    from dmri_pipe_aux import downsample_matrix
    from dmri_pipe_aux import merge_matrices
    from dmri_pipe_aux import transpose_matrix



    fsl.FSLCommand.set_default_output_type('NIFTI')
    
    left_hemi_string = 'lh'
    left_side_string = 'left'
    right_hemi_string = 'rh'
    right_side_string = 'right'

    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    define the workflow
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    dmripipeline = pe.Workflow(name='pipe5_distmnat_' + left_hemi_string + "_" + right_hemi_string)
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Use datasource node to perform the actual data grabbing.
    Templates for the associated images are used to obtain the correct images.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    data_template = subject_ID + "/%s/" + "%s" + "%s"
    
    info = dict(left_roi = [['compact_tracts', subject_ID, '_'+ left_side_string + '.txt']],
                right_roi = [['compact_tracts', subject_ID, '_'+ right_side_string + '.txt']],
                left_fs4_index = [['interface_index', subject_ID, '_seed_index_fs4_' + left_side_string +'.txt']],
                right_fs4_index = [['interface_index', subject_ID, '_seed_index_fs4_' + right_side_string +'.txt']],
                left_fs5_index = [['interface_index', subject_ID, '_seed_index_fs5_' +left_side_string +'.txt']],
                right_fs5_index = [['interface_index', subject_ID, '_seed_index_fs5_' + right_side_string +'.txt']],
                left_full_index = [['interface_index', subject_ID, '_seed_index_fsnative_' + left_side_string +'.txt']],
                right_full_index = [['interface_index', subject_ID, '_seed_index_fsnative_' + right_side_string +'.txt']]
#                 ,fs4_simmat_nat_left = [['similarity_matrix/fs4', subject_ID, '_simmat_fs4_nat_left.nii']],
#                 fs4_simmat_log_left = [['similarity_matrix/fs4', subject_ID, '_simmat_fs4_log_left.nii']],
#                 fs4_simmat_nat_right = [['similarity_matrix/fs4', subject_ID, '_simmat_fs4_nat_right.nii']],
#                 fs4_simmat_log_right = [['similarity_matrix/fs4', subject_ID, '_simmat_fs4_log_right.nii']],
#                 fs5_simmat_nat_left = [['similarity_matrix/fs5', subject_ID, '_simmat_fs5_nat_left.nii']],
#                 fs5_simmat_log_left = [['similarity_matrix/fs5', subject_ID, '_simmat_fs5_log_left.nii']],
#                 fs5_simmat_nat_right = [['similarity_matrix/fs5', subject_ID, '_simmat_fs5_nat_right.nii']],
#                 fs5_simmat_log_right = [['similarity_matrix/fs5', subject_ID, '_simmat_fs5_log_right.nii']]
                )
    
    
    datasource = pe.Node(interface=io.DataGrabber(outfields=info.keys()), name='datasource')
    datasource.inputs.template = data_template
    datasource.inputs.base_directory = output_dir
    datasource.inputs.template_args = info
    datasource.inputs.sort_filelist = True
    datasource.run_without_submitting = True
    
    inputnode = pe.Node(interface=util.IdentityInterface(fields=["left_roi", "right_roi", "left_fs4_index", "right_fs4_index", "left_fs5_index", "right_fs5_index"
#                                                                  ,"fs4_simmat_nat_left","fs4_simmat_log_left","fs4_simmat_nat_right","fs4_simmat_log_right",
#                                                                  "fs5_simmat_nat_left","fs5_simmat_log_left","fs5_simmat_nat_right","fs5_simmat_log_right"
                                                                 ]), name="inputnode")
    
    left_tract_dir_nat = output_dir + "/" + subject_ID + "/compact_tracts/nat/" + left_hemi_string
    right_tract_dir_nat = output_dir + "/" + subject_ID + "/compact_tracts/nat/" + right_hemi_string
    left_tract_dir_log = output_dir + "/" + subject_ID + "/compact_tracts/log/" + left_hemi_string
    right_tract_dir_log = output_dir + "/" + subject_ID + "/compact_tracts/log/" + right_hemi_string

    
    thres_nat = 0.001
    thres_log = np.emath.log10(tract_number*thres_nat) / np.emath.log10(tract_number)

    

    
    """
    compute the full distance matrices
    """
    
    lat_distmat_nat_v = pe.Node(interface=DistMatrixLat(), name='85_lat_distmat_nat')
    lat_distmat_nat_v.inputs.tract_dir_a = left_tract_dir_nat
    lat_distmat_nat_v.inputs.tract_dir_b = right_tract_dir_nat
    lat_distmat_nat_v.inputs.memory = 6
    lat_distmat_nat_v.inputs.threshold = thres_nat
    lat_distmat_nat_v.inputs.out_file = subject_ID + '_full_distmat_nat_' + left_side_string + "_" + right_side_string + '.v'
    lat_distmat_nat_v.run_without_submitting = True
#    lat_distmat_nat.plugin_args={'override_specs': 'requirements = Machine == "kalifornien.cbs.mpg.de"'}
    dmripipeline.connect(inputnode, "left_roi", lat_distmat_nat_v,"roi_file_a")
    dmripipeline.connect(inputnode, "right_roi", lat_distmat_nat_v,"roi_file_b")

    
    lat_distmat_log_v = pe.Node(interface=DistMatrixLat(), name='85_lat_distmat_log')
    lat_distmat_log_v.inputs.tract_dir_a = left_tract_dir_log
    lat_distmat_log_v.inputs.tract_dir_b = right_tract_dir_log
    lat_distmat_log_v.inputs.memory = 6
    lat_distmat_log_v.inputs.threshold = thres_log
    lat_distmat_log_v.inputs.out_file = subject_ID + '_full_distmat_log_'  + left_side_string + "_" + right_side_string + '.v'
    lat_distmat_log_v.run_without_submitting = True
    dmripipeline.connect(inputnode, "left_roi", lat_distmat_log_v,"roi_file_a")
    dmripipeline.connect(inputnode, "right_roi", lat_distmat_log_v,"roi_file_b")    
    """
    transform matrices to .mat format
    """
    
    lat_distmat_nat = pe.Node(interface=vista.VtoMat(), name='86_lat_distmat_nat')
    #lat_distmat_nat.run_without_submitting = True
    dmripipeline.connect(lat_distmat_nat_v, "out_file", lat_distmat_nat,"in_file")
    
    lat_distmat_log = pe.Node(interface=vista.VtoMat(), name='86_lat_distmat_log')
    #lat_distmat_log.run_without_submitting = True
    dmripipeline.connect(lat_distmat_log_v, "out_file", lat_distmat_log,"in_file")
    

    
    """
    downsample matrices according to fsaverage projections
    """
    if (not use_sample):
        sim_mat_fs4_nat = pe.Node(interface=Function(input_names=["index_row_file","index_col_file","matrix_file","out_prefix","dist2sim","transpose"], output_names=["out_mat","out_nii"], function=downsample_matrix), name='87_sim_mat_fs4_nat')
        sim_mat_fs4_nat.inputs.out_prefix = subject_ID + '_simmat_fs4_nat_' + left_side_string + "_" + right_side_string
        sim_mat_fs4_nat.inputs.dist2sim = True
        sim_mat_fs4_nat.inputs.transpose = True
        dmripipeline.connect(inputnode, "left_fs4_index", sim_mat_fs4_nat,"index_row_file")
        dmripipeline.connect(inputnode, "right_fs4_index", sim_mat_fs4_nat,"index_col_file")
        dmripipeline.connect(lat_distmat_nat, "out_file", sim_mat_fs4_nat,"matrix_file")
        
#         sim_mat_fs4_nat_tp = pe.Node(interface=Function(input_names=["in_matrix","out_filename"], output_names=["out_nii"], function=transpose_matrix), name='88_sim_mat_fs4_nat_tp')
#         sim_mat_fs4_nat_tp.inputs.out_filename = subject_ID + '_simmat_fs4_nat_' + left_side_string + "_" + right_side_string + "_tp.nii"
#         dmripipeline.connect(sim_mat_fs4_nat, "out_nii", sim_mat_fs4_nat_tp,"in_matrix")
# 
#         full_simmat_fs4_nat = pe.Node(interface=Function(input_names=["sm_left_left", "sm_left_right","sm_right_left", "sm_right_right", "out_filename"], output_names=["out_file"], function=merge_matrices), name='89_sim_mat_fs4_full_nat')
#         full_simmat_fs4_nat.inputs.out_filename = subject_ID + '_simmat_fs4_nat_full.mat'
#         full_simmat_fs4_nat.run_without_submitting = True
#         dmripipeline.connect(inputnode, "fs4_simmat_nat_left", full_simmat_fs4_nat, "sm_left_left")
#         dmripipeline.connect(sim_mat_fs4_nat, "out_nii", full_simmat_fs4_nat, "sm_left_right")
#         dmripipeline.connect(sim_mat_fs4_nat_tp, "out_nii", full_simmat_fs4_nat, "sm_right_left")
#         dmripipeline.connect(inputnode, "fs4_simmat_nat_right", full_simmat_fs4_nat, "sm_right_right")
        
        
        sim_mat_fs4_log = sim_mat_fs4_nat.clone(name='87_sim_mat_fs4_log')
        sim_mat_fs4_log.inputs.out_prefix = subject_ID + '_simmat_fs4_log_' + left_side_string + "_" + right_side_string 
        dmripipeline.connect(inputnode, "left_fs4_index", sim_mat_fs4_log,"index_row_file")
        dmripipeline.connect(inputnode, "right_fs4_index", sim_mat_fs4_log,"index_col_file")
        dmripipeline.connect(lat_distmat_log, "out_file", sim_mat_fs4_log,"matrix_file")
        
#         sim_mat_fs4_log_tp = sim_mat_fs4_nat_tp.clone(name='88_sim_mat_fs4_log_tp')
#         sim_mat_fs4_log_tp.inputs.out_filename = subject_ID + '_simmat_fs4_log_' + left_side_string + '_' + right_side_string + '_tp.nii'
#         dmripipeline.connect(sim_mat_fs4_log, "out_nii", sim_mat_fs4_log_tp,"in_matrix")
# 
#         full_simmat_fs4_log = full_simmat_fs4_nat.clone(name='89_sim_mat_fs4_full_log')
#         full_simmat_fs4_log.inputs.out_filename = subject_ID + '_simmat_fs4_log_full.mat'
#         full_simmat_fs4_log.run_without_submitting = True
#         dmripipeline.connect(inputnode, "fs4_simmat_log_left", full_simmat_fs4_log, "sm_left_left")
#         dmripipeline.connect(sim_mat_fs4_log, "out_nii", full_simmat_fs4_log, "sm_left_right")
#         dmripipeline.connect(sim_mat_fs4_log_tp, "out_nii", full_simmat_fs4_log, "sm_right_left")
#         dmripipeline.connect(inputnode, "fs4_simmat_log_right", full_simmat_fs4_log, "sm_right_right")

          
        sim_mat_fs5_nat = sim_mat_fs4_nat.clone( name='89_sim_mat_fs5_nat')
        sim_mat_fs5_nat.inputs.out_prefix = subject_ID + '_simmat_fs5_nat_' + left_side_string + "_" + right_side_string 
        dmripipeline.connect(inputnode, "left_fs5_index", sim_mat_fs5_nat,"index_row_file")
        dmripipeline.connect(inputnode, "right_fs5_index", sim_mat_fs5_nat,"index_col_file")
        dmripipeline.connect(lat_distmat_nat, "out_file", sim_mat_fs5_nat,"matrix_file")
        
#         sim_mat_fs5_nat_tp = sim_mat_fs4_nat_tp.clone(name='88_sim_mat_fs5_nat_tp')
#         sim_mat_fs5_nat_tp.inputs.out_filename = subject_ID + '_simmat_fs5_nat_' + left_side_string + "_" + right_side_string + "_tp.nii"
#         dmripipeline.connect(sim_mat_fs5_nat, "out_nii", sim_mat_fs5_nat_tp,"in_matrix")
# 
#         full_simmat_fs5_nat = full_simmat_fs4_nat.clone(name='89_sim_mat_fs5_full_nat')
#         full_simmat_fs5_nat.inputs.out_filename = subject_ID + '_simmat_fs5_nat_full.mat'
#         full_simmat_fs5_nat.run_without_submitting = True
#         dmripipeline.connect(inputnode, "fs5_simmat_nat_left", full_simmat_fs5_nat, "sm_left_left")
#         dmripipeline.connect(sim_mat_fs5_nat, "out_nii", full_simmat_fs5_nat, "sm_left_right")
#         dmripipeline.connect(sim_mat_fs5_nat_tp, "out_nii", full_simmat_fs5_nat, "sm_right_left")
#         dmripipeline.connect(inputnode, "fs5_simmat_nat_right", full_simmat_fs5_nat, "sm_right_right")
        
    
        sim_mat_fs5_log = sim_mat_fs5_nat.clone(  name='89_sim_mat_fs5_log')
        sim_mat_fs5_log.inputs.out_prefix = subject_ID + '_simmat_fs5_log_' + left_side_string + "_" + right_side_string
        dmripipeline.connect(inputnode, "left_fs5_index", sim_mat_fs5_log,"index_row_file")
        dmripipeline.connect(inputnode, "right_fs5_index", sim_mat_fs5_log,"index_col_file")
        dmripipeline.connect(lat_distmat_log, "out_file", sim_mat_fs5_log,"matrix_file")
        
#         sim_mat_fs5_log_tp = sim_mat_fs5_nat_tp.clone(name='88_sim_mat_fs5_log_tp')
#         sim_mat_fs5_log_tp.inputs.out_filename = subject_ID + '_simmat_fs5_log_' + left_side_string + "_" + right_side_string + "_tp.nii"
#         dmripipeline.connect(sim_mat_fs5_log, "out_nii", sim_mat_fs5_log_tp,"in_matrix")
#         
#         full_simmat_fs5_log = full_simmat_fs5_nat.clone(name='89_sim_mat_fs5_full_log')
#         full_simmat_fs5_log.inputs.out_filename = subject_ID + '_simmat_fs5_log_full.mat'
#         full_simmat_fs5_log.run_without_submitting = True
#         dmripipeline.connect(inputnode, "fs5_simmat_log_left", full_simmat_fs5_log, "sm_left_left")
#         dmripipeline.connect(sim_mat_fs5_log, "out_nii", full_simmat_fs5_log, "sm_left_right")
#         dmripipeline.connect(sim_mat_fs5_log_tp, "out_nii", full_simmat_fs5_log, "sm_right_left")
#         dmripipeline.connect(inputnode, "fs5_simmat_log_right", full_simmat_fs5_log, "sm_right_right")

    
    """
    save outputs
    """
    
    datasink = pe.Node(io.DataSink(), name='99_datasink')
    datasink.inputs.base_directory = output_dir
    datasink.inputs.container = subject_ID
    datasink.inputs.parameterization = True
    datasink.run_without_submitting = True
     
    dmripipeline.connect(lat_distmat_nat, 'out_file', datasink, 'similarity_matrix.native')
    dmripipeline.connect(lat_distmat_log, 'out_file', datasink, 'similarity_matrix.native.@1')
    
    if (not use_sample):
        dmripipeline.connect(sim_mat_fs4_nat, 'out_nii', datasink, 'similarity_matrix.fs4.@2')
        dmripipeline.connect(sim_mat_fs4_log, 'out_nii', datasink, 'similarity_matrix.fs4.@3')
        dmripipeline.connect(sim_mat_fs5_nat, 'out_nii', datasink, 'similarity_matrix.fs5.@4')
        dmripipeline.connect(sim_mat_fs5_log, 'out_nii', datasink, 'similarity_matrix.fs5.@6')
#         dmripipeline.connect(sim_mat_fs4_nat, 'out_mat', datasink, 'similarity_matrix.fs4.mat.@2')
#         dmripipeline.connect(sim_mat_fs4_log, 'out_mat', datasink, 'similarity_matrix.fs4.mat.@3')
#         dmripipeline.connect(sim_mat_fs5_nat, 'out_mat', datasink, 'similarity_matrix.fs5.mat.@4')
#         dmripipeline.connect(sim_mat_fs5_log, 'out_mat', datasink, 'similarity_matrix.fs5.mat.@6')
#         dmripipeline.connect(full_simmat_fs4_nat, 'out_file', datasink, 'similarity_matrix.@2')
#         dmripipeline.connect(full_simmat_fs5_nat, 'out_file', datasink, 'similarity_matrix.@3')
#         dmripipeline.connect(full_simmat_fs4_log, 'out_file', datasink, 'similarity_matrix.@4')
#         dmripipeline.connect(full_simmat_fs5_log, 'out_file', datasink, 'similarity_matrix.@6')
    
    
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
    
    connectprepro = pe.Workflow(name="dmri_pipe5_distmat_lr")
    
    connectprepro.base_dir = op.abspath(workflow_dir + "/workflow_"+subject_ID )
    connectprepro.connect([(datasource, dmripipeline, [('left_roi', 'inputnode.left_roi'),('right_roi', 'inputnode.right_roi'),
                                                       ('left_fs4_index', 'inputnode.left_fs4_index'),('right_fs4_index', 'inputnode.right_fs4_index'),
                                                       ('left_fs5_index', 'inputnode.left_fs5_index'),('right_fs5_index', 'inputnode.right_fs5_index')
#                                                        ,('fs4_simmat_nat_left', 'inputnode.fs4_simmat_nat_left'),('fs4_simmat_log_left', 'inputnode.fs4_simmat_log_left'),
#                                                        ('fs4_simmat_nat_right', 'inputnode.fs4_simmat_nat_right'),('fs4_simmat_log_right', 'inputnode.fs4_simmat_log_right'),
#                                                        ('fs5_simmat_nat_left', 'inputnode.fs5_simmat_nat_left'),('fs5_simmat_log_left', 'inputnode.fs5_simmat_log_left'),
#                                                        ('fs5_simmat_nat_right', 'inputnode.fs5_simmat_nat_right'),('fs5_simmat_log_right', 'inputnode.fs5_simmat_log_right')
                                                       ])])
    return connectprepro




