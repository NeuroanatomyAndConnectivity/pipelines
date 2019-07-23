'''
Created on Oct 17, 2013
@author: moreno
'''

#!/usr/bin/env python
"""
=============================================
Diffusion MRI Probabiltic tractography on NKI_enhanced.

This script uses FSL and MRTRIX algorithms to generate probabilstic tracts, tract density images
and  a 3D trackvis file of NKI_enhanced data.
=============================================
"""

def do_cleanup(pipe_id, subject_id, workflow_dir, output_dir):
    import subprocess
    
    if(pipe_id<0 or pipe_id>5):
        return
    
    pipe_names = []
    pipe_names.append('pipe1_prepro')
    pipe_names.append('pipe2_tracts_lh')
    pipe_names.append('pipe2_tracts_rh')
    pipe_names.append('pipe3_projection')
    pipe_names.append('pipe4_distmat_lh')
    pipe_names.append('pipe4_distmat_rh')
    pipe_names.append('pipe5_distmat_lr')
    pipe_names.append('pipe6_decimate2pfc')

    workflow_dirs = []
    workflow_dirs.append(workflow_dir + '/workflow_'+ subject_id + '/dmri_' + pipe_names[0] + '/')
    workflow_dirs.append(workflow_dir + '/workflow_'+ subject_id + '/dmri_' + pipe_names[1] + '/')
    workflow_dirs.append(workflow_dir + '/workflow_'+ subject_id + '/dmri_' + pipe_names[2] + '/')
    workflow_dirs.append(workflow_dir + '/workflow_'+ subject_id + '/dmri_' + pipe_names[3] + '/')
    workflow_dirs.append(workflow_dir + '/workflow_'+ subject_id + '/dmri_' + pipe_names[4] + '/')
    workflow_dirs.append(workflow_dir + '/workflow_'+ subject_id + '/dmri_' + pipe_names[5] + '/')
    workflow_dirs.append(workflow_dir + '/workflow_'+ subject_id + '/dmri_' + pipe_names[6] + '/')
    workflow_dirs.append(workflow_dir + '/workflow_'+ subject_id + '/dmri_' + pipe_names[7] + '/')


    
    subject_output = output_dir + '/' + subject_id + '/'
    
    if( pipe_id == 0):
        subprocess.call('mkdir ' + subject_output + 'graphs', shell=True)
    
    subprocess.call('\cp ' + workflow_dirs[pipe_id] + 'graph.dot.png ' + subject_output + 'graphs/' + pipe_names[pipe_id] + '_graph.png', shell=True)
    subprocess.call('\cp ' + workflow_dirs[pipe_id] + 'graph.dot ' + subject_output + 'graphs/' + pipe_names[pipe_id] + '_graph.dot', shell=True)

    subprocess.call('echo deleting ' + pipe_names[pipe_id] + ' directories... ', shell=True)
    subprocess.call('rm -fr ' + workflow_dirs[pipe_id], shell=True)
    
    return


def do_wrapup(subject_id, workflow_dir, output_dir):
    import subprocess
    
    subprocess.call('echo deleting workflow directories... ', shell=True)
    subprocess.call('rm -fr ' + workflow_dir + '/workflow_'+ subject_id, shell=True)
    
    subprocess.call('echo renaming diff data files... ', shell=True)
    sub_diff = output_dir + '/' + subject_id + '/diff_data/'
    subprocess.call('mv -f ' + sub_diff +'vol0000_flirt_merged.nii ' + sub_diff + subject_id + '_diff_moco.nii', shell=True)
    subprocess.call('gzip -f ' + sub_diff + subject_id + '_diff_moco.nii', shell=True)
    subprocess.call('mv -f ' + sub_diff +'*_thresholded_100.txt ' + sub_diff +'bval_bvec.txt', shell=True )
     
    subprocess.call('echo compressing diff model files... ', shell=True)
    sub_model = output_dir + '/' + subject_id + '/diff_model/'
    subprocess.call('gzip -f ' + sub_model + subject_id + '_CSD.mif', shell=True)
    subprocess.call('gzip -f ' + sub_model + subject_id + '_CSD_tracked.tck', shell=True)

    subprocess.call('echo compressing left hemisphere tracts... ', shell=True)
    subprocess.call('gzip -f ' + output_dir + '/' + subject_id + '/raw_tracts/lh/*.nii', shell=True)
 
    subprocess.call('echo compressing right hemisphere tracts... ', shell=True)
    subprocess.call('gzip -f ' + output_dir + '/' + subject_id + '/raw_tracts/rh/*.nii', shell=True)
    
    subprocess.call('echo compressing direct connectivity matrices... ', shell=True)
    subprocess.call('gzip -f ' + output_dir + '/' + subject_id + '/connect_matrix/native/*.mat', shell=True)
    subprocess.call('gzip -f ' + output_dir + '/' + subject_id + '/connect_matrix/native/*.nii', shell=True)
    subprocess.call('gzip -f ' + output_dir + '/' + subject_id + '/connect_matrix/fs*/mat/*.mat', shell=True)
    subprocess.call('gzip -f ' + output_dir + '/' + subject_id + '/connect_matrix/fs*/*.nii', shell=True)
    
    subprocess.call('echo compressing similarity matrices... ', shell=True)
    subprocess.call('gzip -f ' + output_dir + '/' + subject_id + '/similarity_matrix/native/*.mat', shell=True)
    subprocess.call('gzip -f ' + output_dir + '/' + subject_id + '/similarity_matrix/native/*.nii', shell=True)
    subprocess.call('gzip -f ' + output_dir + '/' + subject_id + '/similarity_matrix/fs*/mat/*.mat', shell=True)
    subprocess.call('gzip -f ' + output_dir + '/' + subject_id + '/similarity_matrix/fs*/*.nii', shell=True)

    subprocess.call('echo ALL DONE for ' + subject_id + '!!!', shell=True)
    
    
    return

    
    