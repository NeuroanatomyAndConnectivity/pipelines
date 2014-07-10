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

# fslswapdim A_diff_moco.nii -x y z A_diff_moco_NEUROLOGICAL.nii.gz
# fslorient -swaporient A_diff_moco_NEUROLOGICAL.nii
# some_command | tee >(command1) >(command2) >(command3) ... | command4

if __name__ == '__main__':
    
    import sys
    import datetime, time
    from nipype import config
    
    from dmri_pipe1_prepro import do_pipe1_prepro
    from dmri_pipe2_tractscript import script_tracking, trackwait
    from dmri_pipe3_projection import do_pipe3_projection
    from dmri_pipe4_distmat import do_pipe4_distmat
    from dmri_pipe5_distmat_lr import do_pipe5_distmat_lr
    from dmri_pipe_cleanup import do_cleanup, do_wrapup

    cfg = dict(logging=dict(workflow_level = 'INFO'), execution={'remove_unnecessary_outputs': False, 'job_finished_timeout': 120, 'stop_on_first_rerun': False, 'stop_on_first_crash': True} )
    config.update_config(cfg)
    
    tract_number = 5000
    tract_step = 0.3
    freesurfer_dir = '/scr/kalifornien1/data/nki_enhanced/freesurfer'
    data_dir = '/scr/kalifornien1/data/nki_enhanced/dicoms/diff_2_nii'
#    freesurfer_dir = '/scr/kongo2/NKI_ENH/freesurfer'
#    data_dir = '/scr/kongo2/NKI_ENH/dMRI'
    
    data_template = "%s/DTI_mx_137/%s"
    is_LH = True
    is_RH = False
    pipe_dict = dict([('0',0),('1',0),('2',1),('21',1),('22',2),('3',3),('4',4),('41',4),('42',5),('5',6)])
    pipe_stop = 7

    
    """
    PIPE VARIABLES BELOW
    """
    use_sample = False
    use_condor = True
    clean = True
    pipe_start = '3'
    pipe_restart= '2'
    



    subject_list = ["0114232"]
    
    
    remaining=["0115321","0102157","0103872","0109459","0115454","0115564","0115684","0115824","0116039","0116065",
                    "0116415","0116834","0116842","0117168","0117902","0117964","0118051","0119351","0119866"]
    
    
    remaining_subjects = []
        
    done_subjects_0 =  ['0102157','0103645','0105290','0105488','0105521','0106057','0106780','0108184','0108355']
    done_subjects_0b = ['0103872','0108781','0109727','0109459','0109819']
    done_subjects_6 =  ['0168239']
    done_subjects_8 =  ['0188939']
    
    done_subjects_1_bad_sim =["0113013"]
    done_subjects_1 =["0111282","0112249","0112347","0112536""0112828",    "0113030","0114008","0114232"]
    
    """
    END PIPE VARIABLES
    """
    start_point = pipe_dict.get(pipe_start,pipe_stop)
    restart_point = pipe_dict.get(pipe_restart,pipe_stop)  


    if (use_sample):
        workflow_dir = '/scr/kongo2/moreno_nipype/dmri_workflow_sample'
        output_dir = '/scr/kongo2/moreno_nipype/NKI_dMRI_output_sample'
        chunk_nr = 1
    else:
        workflow_dir = '/scr/kongo2/moreno_nipype/dmri_workflow'
        output_dir = '/scr/kongo2/NKI_dMRI_output'
        chunk_nr = 100

        

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    loop through the subject list and define the input files.
    For our purposes, these are the dwi image, b vectors, and b values.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    
        
    for subject_id in subject_list:
        
       
        if(clean):
            do_wrapup(subject_id, workflow_dir, output_dir)
        start_point = restart_point  #start next subject from first pipeline
        
