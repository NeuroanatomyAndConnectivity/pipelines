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
    pipe_start = '2'
    pipe_restart= '2'
    

                    
    subject_list = ["0117168","0117902","0117964","0118051","0119351","0119866"] 
    remaining_subjects = ["0102157","0116415","0116834","0116842"]
        

    done_subjects_0 = ["0103645","0103872","0105290","0105488","0105521","0106057","0106780","0108184","0108355","0108781","0109459","0109727","0109819"]
    done_subjects_1 = ["0111282","0112249","0112347","0112536","0112828","0113013","0113030","0114008","0114232","0115321","0115454","0115564","0115684",
                       "0115824","0116039","0116065"]
    done_subjects_6 =  ["0168239"]
    done_subjects_8 =  ["0188939"]
    
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
    
        
    for sub_pos in xrange(len(subject_list)):
        
        subject_id = subject_list[sub_pos]
        next_id = subject_list[sub_pos+1]
        workflow_0_prepro = do_pipe1_prepro(subject_id, freesurfer_dir, data_dir, data_template, workflow_dir, output_dir)

        workflow_3_proj = do_pipe3_projection(subject_id, freesurfer_dir, workflow_dir, output_dir, tract_number, use_sample)
        workflow_4_distmat_lh = do_pipe4_distmat(subject_id, workflow_dir, output_dir, tract_number, is_LH, use_sample)
        workflow_5_distmat_rh = do_pipe4_distmat(subject_id, workflow_dir, output_dir, tract_number, is_RH, use_sample)
        workflow_6_distmat_lr = do_pipe5_distmat_lr(subject_id, workflow_dir, output_dir, tract_number, use_sample)
     
        if (use_condor):
            this_plugin='Condor'
            #this_plugin='CondorDAGMan'
        else:
            this_plugin='Linear'
            
        for i in xrange(pipe_stop):
            if (i<start_point):
                continue
            
            


            if(i==0 or i>2):
                if(i==0):
                    cfghash = dict(execution={'hash_method': "content"} )
                    if (use_condor):
                        this_plugin='Condor'
                        #this_plugin='CondorDAGMan'
                    else:
                        this_plugin='Linear'
                    this_workflow=workflow_0_prepro
                elif (i==3):
                    cfghash = dict(execution={'hash_method': "timestamp"} )
                    this_plugin='MultiProc'
                    this_workflow=workflow_3_proj
                elif (i==4):
                    cfghash = dict(execution={'hash_method': "timestamp"} )
                    this_plugin='MultiProc'
                    this_workflow=workflow_4_distmat_lh
                elif (i==5):
                    cfghash = dict(execution={'hash_method': "timestamp"} )
                    this_plugin='MultiProc'
                    this_workflow=workflow_5_distmat_rh
                elif (i==6):
                    cfghash = dict(execution={'hash_method': "timestamp"} )
                    this_plugin='MultiProc'
                    this_workflow=workflow_6_distmat_lr
                    
                config.update_config(cfghash)
                    
                this_workflow.write_graph()
                runtime_err_counter = 0
                while True:
                    try:
                        this_workflow.run(plugin=this_plugin, plugin_args={'block':True})
                        break
                    except IOError as io_error:
                        this_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                        error_message = "***********\nIO EXCEPTION ERROR AT: {0}\nSubject: {1} workflow: {2}, RE-RUNNING WORKFLOW\n{3}\n***********\n".format(this_time, subject_id, i, sys.exc_info())
                        print error_message                     
                        errorlog_file = open(workflow_dir + '/'+ subject_id +'_IO_exceptions.log','a')
                        errorlog_file.write( error_message )
                        errorlog_file.close()
                    except RuntimeError as runtime_error:
                        this_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                        error_message = "***********\nRUNTIME EXCEPTION ERROR AT: {0}\nSubject: {1} workflow: {2}, RE-RUNNING WORKFLOW\n{3}\n***********\n".format(this_time, subject_id, i, sys.exc_info())
                        print error_message
                        errorlog_file = open(workflow_dir + '/'+ subject_id +'_runtime_exceptions.log','a')
                        errorlog_file.write( error_message )
                        errorlog_file.close()
                        runtime_err_counter += 1
                        if (runtime_err_counter > 10):
                            raise
                    except:
                        this_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                        error_message = "***********\nUNEXPECTED ERROR AT: {0}\nSubject: {1} workflow: {2}\n{3}\n***********\n".format(this_time, subject_id, i, sys.exc_info())
                        print error_message
                        errorlog_file = open(workflow_dir + '/'+ subject_id +'_unknown_exceptions.log','a')
                        errorlog_file.write( error_message )
                        errorlog_file.close()
                        raise
                if(clean):
                    do_cleanup(i, subject_id, workflow_dir, output_dir)
                    
            else: #its the scripting part
                if(i==1):
                    script_tracking(next_id, chunk_nr, output_dir, tract_number,tract_step, is_LH, use_sample)
                elif (i==2):
                    script_tracking(next_id, chunk_nr, output_dir, tract_number,tract_step, is_RH, use_sample)
        #end if else about which workflow
       
        if(clean):
            do_wrapup(subject_id, workflow_dir, output_dir)
        start_point = restart_point  #start next subject from first pipeline
        trackwait(next_id, chunk_nr, output_dir)
        print("loop complete. continuing\n")
        
