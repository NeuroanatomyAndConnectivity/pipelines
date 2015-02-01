from nipype.pipeline.engine import Workflow, Node
import nipype.interfaces.utility as util
import nipype.interfaces.freesurfer as fs

'''
Workflow to run freesurfer recon-all -all and collect original output
'''


def create_reconall_pipeline(name='reconall'):
    
    reconall=Workflow(name='reconall')

    #inputnode 
    inputnode=Node(util.IdentityInterface(fields=['anat', 
                                                  'fs_subjects_dir',
                                                  'fs_subject_id'
                                                  ]),
                   name='inputnode')
    
    outputnode=Node(util.IdentityInterface(fields=['fs_subjects_dir',
                                                   'fs_subject_id']),
                    name='outputnode')
    
    # run reconall
    recon_all = Node(fs.ReconAll(args='-nuiterations 7 -no-isrunning'),
                     name="recon_all")
    recon_all.plugin_args={'submit_specs': 'request_memory = 9000'}
    
    # function to replace / in subject id string with a _
    def sub_id(sub_id):
        return sub_id.replace('/','_')
    
    reconall.connect([(inputnode, recon_all, [('fs_subjects_dir', 'subjects_dir'),
                                              ('anat', 'T1_files'),
                                              (('fs_subject_id', sub_id), 'subject_id')]),
                      (recon_all, outputnode, [('subject_id', 'fs_subject_id'),
                                               ('subjects_dir', 'fs_subjects_dir')])
                      ])
    
    
    return reconall