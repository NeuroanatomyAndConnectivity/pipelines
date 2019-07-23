from nipype.pipeline.engine import MapNode, Node, Workflow
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl
import nipype.algorithms.misc as misc

'''
Workflow for motion correction to 1st volume and tSNR
'''

def create_moco_pipeline(name='motion_correction'):
    
    # initiate workflow
    moco=Workflow(name='motion_correction')
    
    # set fsl output
    fsl.FSLCommand.set_default_output_type('NIFTI_GZ')
    
    # inputnode
    inputnode = Node(util.IdentityInterface(fields=['epi']),
                     name='inputnode')
    
    # outputnode
    outputnode = Node(util.IdentityInterface(fields=['epi_moco', 
                                                     'par_moco', 
                                                     'mat_moco', 
                                                     'rms_moco',
                                                     'epi_mean', 
                                                     'rotplot', 
                                                     'transplot',
                                                     'dispplots',
                                                     'tsnr_file']),
                      name='outputnode')
    
    # mcflirt motion correction to 1st volume
    mcflirt = Node(fsl.MCFLIRT(save_mats=True,
                               save_plots=True,
                               save_rms=True,
                               ref_vol=1,
                               out_file='rest_realigned.nii.gz'
                               ),
                   name='mcflirt')
    
    # plot motion parameters
    rotplotter = Node(fsl.PlotMotionParams(in_source='fsl',
                                   plot_type='rotations',
                                   out_file='rotation_plot.png'),
                      name='rotplotter')
    
    
    transplotter = Node(fsl.PlotMotionParams(in_source='fsl',
                                     plot_type='translations',
                                     out_file='translation_plot.png'),
                        name='transplotter')

    dispplotter = MapNode(interface=fsl.PlotMotionParams(in_source='fsl',
                                                         plot_type='displacement',
                                                         ),
                            name='dispplotter',
                            iterfield=['in_file'])
    dispplotter.iterables = ('plot_type', ['displacement'])
    
    # calculate tmean
    tmean = Node(fsl.maths.MeanImage(dimension='T',
                                     out_file='rest_realigned_mean.nii.gz'),
                 name='tmean')
    
    # calculate tsnr
    tsnr = Node(misc.TSNR(),
                name='tsnr')
    
    # create connections
    moco.connect([(inputnode, mcflirt, [('epi', 'in_file')]),
                  (mcflirt, tmean, [('out_file', 'in_file')]),
                  (mcflirt, rotplotter, [('par_file', 'in_file')]),
                  (mcflirt, transplotter, [('par_file', 'in_file')]),
                  (mcflirt, dispplotter, [('rms_files', 'in_file')]),
                  (tmean, outputnode, [('out_file', 'epi_mean')]),
                  (mcflirt, outputnode, [('out_file','epi_moco'),
                                         ('par_file','par_moco'),
                                         ('mat_file','mat_moco'),
                                         ('rms_files','rms_moco')]),
                  (rotplotter, outputnode, [('out_file', 'rotplot')]),
                  (transplotter,  outputnode, [('out_file', 'transplot')]),
                  (dispplotter,  outputnode, [('out_file', 'dispplots')]),
                  (mcflirt, tsnr, [('out_file', 'in_file')]),
                  (tsnr, outputnode, [('tsnr_file', 'tsnr_file')])
                  ])
        
        
    return moco

    
    
    