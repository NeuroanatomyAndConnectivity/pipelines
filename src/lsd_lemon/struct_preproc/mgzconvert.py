from nipype.pipeline.engine import Node, Workflow
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl


'''
Workflow to extract relevant output from freesurfer directory
'''

def create_mgzconvert_pipeline(name='mgzconvert'):
    
    # workflow
    mgzconvert = Workflow(name='mgzconvert')

    #inputnode 
    inputnode=Node(util.IdentityInterface(fields=['fs_subjects_dir',
                                                  'fs_subject_id'
                                                  ]),
                   name='inputnode')
    
    #outputnode
    outputnode=Node(util.IdentityInterface(fields=['anat_head',
                                                   'anat_brain',
                                                   'brain_mask',
                                                   'wmseg',
                                                   'wmedge']),
                    name='outputnode')
    

    # import files from freesurfer
    fs_import = Node(interface=nio.FreeSurferSource(),
                     name = 'fs_import')
    
    
    # convert Freesurfer T1 file to nifti
    head_convert=Node(fs.MRIConvert(out_type='niigz',
                                     out_file='T1.nii.gz'),
                       name='head_convert')
    
    # create brainmask from aparc+aseg with single dilation
    def get_aparc_aseg(files):
        for name in files:
            if 'aparc+aseg' in name:
                return name

    brainmask = Node(fs.Binarize(min=0.5,
                                 dilate=1,
                                 out_type='nii.gz'),
                   name='brainmask')


    # fill holes in mask, smooth, rebinarize
    fillholes = Node(fsl.maths.MathsCommand(args='-fillh -s 3 -thr 0.1 -bin',
                                            out_file='T1_brain_mask.nii.gz'),
                     name='fillholes')
    
    
    # mask T1 with the mask
    brain = Node(fsl.ApplyMask(out_file='T1_brain.nii.gz'),
                 name='brain')

    # cortical and cerebellar white matter volumes to construct wm edge
    # [lh cerebral wm, lh cerebellar wm, rh cerebral wm, rh cerebellar wm, brain stem]
    wmseg = Node(fs.Binarize(out_type='nii.gz',
                             match = [2, 7, 41, 46, 16],
                             binary_file='T1_brain_wmseg.nii.gz'), 
                name='wmseg')
    
    # make edge from wmseg  to visualize coregistration quality
    edge = Node(fsl.ApplyMask(args='-edge -bin',
                              out_file='T1_brain_wmedge.nii.gz'),
                name='edge')

    # connections
    mgzconvert.connect([(inputnode, fs_import, [('fs_subjects_dir','subjects_dir'),
                                                ('fs_subject_id', 'subject_id')]),
                        (fs_import, brainmask, [(('aparc_aseg', get_aparc_aseg), 'in_file')]),
                        (fs_import, head_convert, [('T1', 'in_file')]),
                        (fs_import, wmseg, [(('aparc_aseg', get_aparc_aseg), 'in_file')]),
                        (brainmask, fillholes, [('binary_file', 'in_file')]),
                        (fillholes, brain, [('out_file', 'mask_file')]),
                        (head_convert, brain, [('out_file', 'in_file')]),
                        (wmseg, edge, [('binary_file', 'in_file'),
                                       ('binary_file', 'mask_file')]),
                        (head_convert, outputnode, [('out_file', 'anat_head')]),
                        (fillholes, outputnode, [('out_file', 'brain_mask')]),
                        (brain, outputnode, [('out_file', 'anat_brain')]),
                        (wmseg, outputnode, [('binary_file', 'wmseg')]),
                        (edge, outputnode, [('out_file', 'wmedge')])
                        ])
                                         
    return mgzconvert