from nipype.pipeline.engine import Node, Workflow
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs


'''
Workflow calculating fieldmap correction and coregistration
'''

def create_fmap_coreg_pipeline(name='fmap_coreg'):
    
    # fsl output type
    fsl.FSLCommand.set_default_output_type('NIFTI_GZ')
    
    # initiate workflow
    fmap_coreg = Workflow(name='fmap_coreg')
    
    #inputnode 
    inputnode=Node(util.IdentityInterface(fields=['epi_mean',
                                                  'mag',
                                                  'phase',
                                                  'anat_head',
                                                  'anat_brain',
                                                  'fs_subject_id',
                                                  'fs_subjects_dir',
                                                  'echo_space',
                                                  'te_diff',
                                                  'pe_dir'
                                                  ]),
                   name='inputnode')
    
    # outputnode                                     
    outputnode=Node(util.IdentityInterface(fields=['fmap',
                                                   'shiftmap',
                                                   'unwarpfield_epi2fmap',
                                                   'unwarped_mean_epi2fmap',
                                                   'epi2anat_mat',
                                                   'epi2anat_dat',
                                                   'epi2anat_mincost',
                                                   'epi2anat',
                                                   'epi2fmap',
                                                   'fmap_fullwarp']),
                    name='outputnode')
    
    
    #### prepare fieldmap ####
    # split first magnitude image from mag input
    split = Node(fsl.ExtractROI(t_min=0,
                                t_size=1),
                 name='split')
    fmap_coreg.connect(inputnode, 'mag', split, 'in_file')
    
    # strip magnitude image and erode even further
    bet = Node(fsl.BET(frac=0.5,
                       mask=True),
               name='bet')
    fmap_coreg.connect(split,'roi_file', bet,'in_file')
    
    erode = Node(fsl.maths.ErodeImage(kernel_shape='sphere',
                                     kernel_size=3,
                                     args=''),
                name='erode')
    fmap_coreg.connect(bet,'out_file', erode, 'in_file')
    
    # prepare fieldmap
    prep_fmap = Node(fsl.epi.PrepareFieldmap(),
                     name='prep_fmap')
    fmap_coreg.connect([(erode, prep_fmap, [('out_file', 'in_magnitude')]),
                     (inputnode, prep_fmap, [('phase', 'in_phase'),
                                             ('te_diff', 'delta_TE')]),
                     (prep_fmap, outputnode, [('out_fieldmap','fmap')])
                     ])
    
    
    #### unmask fieldmap ####
    fmap_mask = Node(fsl.maths.MathsCommand(args='-abs -bin'),
                     name='fmap_mask')
    
    unmask = Node(fsl.FUGUE(save_unmasked_fmap=True),
                 name='unmask')
    
    fmap_coreg.connect([(prep_fmap, fmap_mask, [('out_fieldmap', 'in_file')]),
                     (fmap_mask, unmask, [('out_file', 'mask_file')]),
                     (prep_fmap, unmask,[('out_fieldmap','fmap_in_file')]),
                     (inputnode, unmask, [('pe_dir', 'unwarp_direction')])
                     ])
    
    #### register epi to fieldmap ####
    epi2fmap = Node(fsl.FLIRT(dof=6,
                              out_file='rest_mean2fmap.nii.gz',
                              interp='spline'),
                    name='epi2fmap')
    
    fmap_coreg.connect([(inputnode,epi2fmap,[('epi_mean', 'in_file')]),
                        (split, epi2fmap, [('roi_file', 'reference')]),
                        (epi2fmap, outputnode, [('out_file', 'epi2fmap')])
                   ])
    
    #### unwarp epi with fieldmap ####
    unwarp = Node(fsl.FUGUE(save_shift=True),
                 name='unwarp')
    
    fmap_coreg.connect([(epi2fmap, unwarp, [('out_file', 'in_file')]),
                     (unmask, unwarp, [('fmap_out_file', 'fmap_in_file')]),
                     (fmap_mask, unwarp, [('out_file','mask_file')]),
                     (inputnode, unwarp, [('echo_space', 'dwell_time'),
                                          ('pe_dir', 'unwarp_direction')]),
                     (unwarp, outputnode, [('shift_out_file', 'shiftmap')])
                     ])
    
    #### make warpfield and apply ####
    convertwarp0 =  Node(fsl.utils.ConvertWarp(out_relwarp=True,
                                              out_file='rest_mean2fmap_unwarpfield.nii.gz'),
                         name='convertwarp0')
       
    applywarp0 = Node(fsl.ApplyWarp(interp='spline',
                                   relwarp=True,
                                   out_file='rest_mean2fmap_unwarped.nii.gz', 
                                   datatype='float'),
                     name='applywarp0') 
       
    fmap_coreg.connect([(split, convertwarp0, [('roi_file', 'reference')]),
                     (epi2fmap, convertwarp0, [('out_matrix_file', 'premat')]),
                     (unwarp, convertwarp0, [('shift_out_file', 'shift_in_file')]),
                     (inputnode, convertwarp0, [('pe_dir', 'shift_direction')]),
                     (inputnode, applywarp0, [('epi_mean', 'in_file')]),
                     (split, applywarp0, [('roi_file', 'ref_file')]),
                     (convertwarp0, applywarp0, [('out_file', 'field_file')]),
                     (convertwarp0, outputnode, [('out_file', 'unwarpfield_epi2fmap')]),
                     (applywarp0, outputnode, [('out_file', 'unwarped_mean_epi2fmap')])
                  ])
    
    #### register epi to anatomy #####
    # linear registration with bbregister
    bbregister = Node(fs.BBRegister(contrast_type='t2',
                                    out_fsl_file='rest2anat.mat',
                                    out_reg_file='rest2anat.dat',
                                    registered_file='rest_mean2anat_highres.nii.gz',
                                    init='fsl',
                                    epi_mask=True
                                    ),
                    name='bbregister')
    
    fmap_coreg.connect([(applywarp0, bbregister, [('out_file', 'source_file')]),
                        (inputnode, bbregister, [('fs_subjects_dir', 'subjects_dir'),
                                                 ('fs_subject_id', 'subject_id')]),
                        (bbregister, outputnode, [('out_fsl_file', 'epi2anat_mat'),
                                                  ('out_reg_file', 'epi2anat_dat'),
                                                  ('registered_file', 'epi2anat'),
                                                  ('min_cost_file', 'epi2anat_mincost')
                                                  ]),
                        ])

    # make warpfield
    convertwarp =  Node(fsl.utils.ConvertWarp(out_relwarp=True,
                                              out_file='fullwarpfield.nii.gz'),
                         name='convertwarp')
  
    fmap_coreg.connect([(inputnode, convertwarp, [('anat_head', 'reference')]),
                     (convertwarp0, convertwarp, [('out_file', 'warp1')]),
                     (bbregister, convertwarp, [('out_fsl_file', 'postmat')]),
                     (convertwarp, outputnode, [('out_file', 'fmap_fullwarp')])
                  ])
    
    return fmap_coreg