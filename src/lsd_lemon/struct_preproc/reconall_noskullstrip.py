from nipype.pipeline.engine import Workflow, Node
import nipype.interfaces.utility as util
import nipype.interfaces.freesurfer as fs
from nipype.workflows.smri.freesurfer import create_skullstripped_recon_flow

'''
Workflow to run freesurfer recon-all WITHOUT SKULLSTRIP 
and collect original output
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
    recon_all = create_skullstripped_recon_flow()
    
    
    # function to replace / in subject id string with a _
    def sub_id(sub_id):
        return sub_id.replace('/','_')
    
    reconall.connect([(inputnode, recon_all, [('fs_subjects_dir', 'inputspec.subjects_dir'),
                                              ('anat', 'inputspec.T1_files'),
                                              (('fs_subject_id', sub_id), 'inputspec.subject_id')]),
                      (recon_all, outputnode, [('outputspec.subject_id', 'fs_subject_id'),
                                               ('outputspec.subjects_dir', 'fs_subjects_dir')])
                      ])
    
    
    return reconall