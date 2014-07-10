'''
Created on Oct 17, 2013

@author: moreno
'''


def do_pipe4_distmat(subject_ID, workflow_dir, output_dir, tract_number, is_left, use_sample=False):

    
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
    from my_custom_interfaces import DistMatrix
    from dmri_pipe_aux import downsample_matrix
    from dmri_pipe_aux import merge_matrices



    fsl.FSLCommand.set_default_output_type('NIFTI')
    
    if (is_left):
        hemi_string = 'lh'
        side_string = 'left'
    else:
        hemi_string = 'rh'
        side_string = 'right'
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    define the workflow
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
    dmripipeline = pe.Workflow(name='pipe4_distmnat_' + hemi_string)
    
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Use datasource node to perform the actual data grabbing.
    Templates for the associated images are used to obtain the correct images.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    data_template = subject_ID + "/%s/" + "%s" + "%s"
    
    info = dict(roi = [['compact_tracts', subject_ID, '_'+ side_string + '.txt']],
                fs4_index = [['interface_index', subject_ID, '_seed_index_fs4_' + side_string +'.txt']],
                fs5_index = [['interface_index', subject_ID, '_seed_index_fs5_' + side_string +'.txt']],
                full_index = [['interface_index', subject_ID, '_seed_index_fsnative_' + side_string +'.txt']])
    
    
    datasource = pe.Node(interface=io.DataGrabber(outfields=info.keys()), name='datasource')
    datasource.inputs.template = data_template
    datasource.inputs.base_directory = output_dir
    datasource.inputs.template_args = info
    datasource.inputs.sort_filelist = True
    datasource.run_without_submitting = True
    
    inputnode = pe.Node(interface=util.IdentityInterface(fields=["roi", "fs4_index", "fs5_index"]), name="inputnode")
    
    tract_dir_nat = output_dir + "/" + subject_ID + "/compact_tracts/nat/" + hemi_string
    tract_dir_log = output_dir + "/" + subject_ID + "/compact_tracts/log/" + hemi_string
    
    thres_nat = 0.001
    thres_log = np.emath.log10(tract_number*thres_nat) / np.emath.log10(tract_number)

    

    
    """
    compute the full distance matrices
    """
    
    full_distmat_nat = pe.Node(interface=DistMatrix(), name='85_full_distmat_nat')
    full_distmat_nat.inputs.tract_dir = tract_dir_nat
    full_distmat_nat.inputs.memory = 6
    full_distmat_nat.inputs.threshold = thres_nat
    full_distmat_nat.inputs.out_file = subject_ID + '_full_distmat_nat_' + side_string + '.v'
    full_distmat_nat.run_without_submitting = True
#    full_distmat_nat.plugin_args={'override_specs': 'requirements = Machine == "kalifornien.cbs.mpg.de"'}
    dmripipeline.connect(inputnode, "roi", full_distmat_nat,"roi_file")
    
    full_distmat_log = pe.Node(interface=DistMatrix(), name='85_full_distmat_log')
    full_distmat_log.inputs.tract_dir = tract_dir_log
    full_distmat_log.inputs.memory = 6
    full_distmat_log.inputs.threshold = thres_log
    full_distmat_log.inputs.out_file = subject_ID + '_full_distmat_log_' + side_string  + '.v'
    full_distmat_log.run_without_submitting = True
    dmripipeline.connect(inputnode, "roi", full_distmat_log,"roi_file")
    
    """
    transform matrices to .mat format
    """
    
    mat_distmat_nat = pe.Node(interface=vista.VtoMat(), name='86_mat_distmat_nat')
    #mat_distmat_nat.run_without_submitting = True
    dmripipeline.connect(full_distmat_nat, "out_file", mat_distmat_nat,"in_file")
    
    mat_distmat_log = pe.Node(interface=vista.VtoMat(), name='86_mat_distmat_log')
    #mat_distmat_log.run_without_submitting = True
    dmripipeline.connect(full_distmat_log, "out_file", mat_distmat_log,"in_file")
    
    """
    downsample matrices according to fsaverage projections
    """
    if (not use_sample):
        sim_mat_fs4_nat = pe.Node(interface=Function(input_names=["index_row_file","index_col_file","matrix_file","out_prefix","dist2sim","transpose"], output_names=["out_mat","out_nii"], function=downsample_matrix), name='87_sim_mat_fs4_nat')
        sim_mat_fs4_nat.inputs.out_prefix = subject_ID + '_simmat_fs4_nat_' + side_string
        sim_mat_fs4_nat.inputs.dist2sim = True
        sim_mat_fs4_nat.inputs.transpose = True
        dmripipeline.connect(inputnode, "fs4_index", sim_mat_fs4_nat,"index_row_file")
        dmripipeline.connect(inputnode, "fs4_index", sim_mat_fs4_nat,"index_col_file")
        dmripipeline.connect(mat_distmat_nat, "out_file", sim_mat_fs4_nat,"matrix_file")
    
        sim_mat_fs4_log = sim_mat_fs4_nat.clone(name='87_sim_mat_fs4_log')
        sim_mat_fs4_log.inputs.out_prefix = subject_ID + '_simmat_fs4_log_' + side_string 
        dmripipeline.connect(inputnode, "fs4_index", sim_mat_fs4_log,"index_row_file")
        dmripipeline.connect(inputnode, "fs4_index", sim_mat_fs4_log,"index_col_file")
        dmripipeline.connect(mat_distmat_log, "out_file", sim_mat_fs4_log,"matrix_file")
        
        sim_mat_fs5_nat = sim_mat_fs4_nat.clone( name='88_sim_mat_fs5_nat')
        sim_mat_fs5_nat.inputs.out_prefix = subject_ID + '_simmat_fs5_nat_' + side_string 
        dmripipeline.connect(inputnode, "fs5_index", sim_mat_fs5_nat,"index_row_file")
        dmripipeline.connect(inputnode, "fs5_index", sim_mat_fs5_nat,"index_col_file")
        dmripipeline.connect(mat_distmat_nat, "out_file", sim_mat_fs5_nat,"matrix_file")
    
        sim_mat_fs5_log = sim_mat_fs5_nat.clone(  name='88_sim_mat_fs5_log')
        sim_mat_fs5_log.inputs.out_prefix = subject_ID + '_simmat_fs5_log_' + side_string
        dmripipeline.connect(inputnode, "fs5_index", sim_mat_fs5_log,"index_row_file")
        dmripipeline.connect(inputnode, "fs5_index", sim_mat_fs5_log,"index_col_file")
        dmripipeline.connect(mat_distmat_log, "out_file", sim_mat_fs5_log,"matrix_file")

    
    """
    save outputs
    """
    
    datasink = pe.Node(io.DataSink(), name='99_datasink')
    datasink.inputs.base_directory = output_dir
    datasink.inputs.container = subject_ID
    datasink.inputs.parameterization = True
    #datasink.run_without_submitting = True
     
    dmripipeline.connect(mat_distmat_nat, 'out_file', datasink, 'similarity_matrix.native')
    dmripipeline.connect(mat_distmat_log, 'out_file', datasink, 'similarity_matrix.native.@1')
    
    if (not use_sample):
        dmripipeline.connect(sim_mat_fs4_nat, 'out_nii', datasink, 'similarity_matrix.fs4.@2')
        dmripipeline.connect(sim_mat_fs4_log, 'out_nii', datasink, 'similarity_matrix.fs4.@4')
        dmripipeline.connect(sim_mat_fs5_nat, 'out_nii', datasink, 'similarity_matrix.fs5.@5')
        dmripipeline.connect(sim_mat_fs5_log, 'out_nii', datasink, 'similarity_matrix.fs5.@7')
#         dmripipeline.connect(sim_mat_fs4_nat, 'out_mat', datasink, 'similarity_matrix.fs4.mat.@2')
#         dmripipeline.connect(sim_mat_fs4_log, 'out_mat', datasink, 'similarity_matrix.fs4.mat.@3')
#         dmripipeline.connect(sim_mat_fs5_nat, 'out_mat', datasink, 'similarity_matrix.fs5.mat.@5')
#         dmripipeline.connect(sim_mat_fs5_log, 'out_mat', datasink, 'similarity_matrix.fs5.mat.@6')
   
    
    
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
    
    connectprepro = pe.Workflow(name="dmri_pipe4_distmat_" + hemi_string)
    
    connectprepro.base_dir = op.abspath(workflow_dir + "/workflow_"+subject_ID )
    connectprepro.connect([(datasource, dmripipeline, [('roi', 'inputnode.roi'),('fs4_index', 'inputnode.fs4_index'),('fs5_index', 'inputnode.fs5_index')])])

    return connectprepro




