def create_dcmconvert_pipeline(name='dcmconvert'):
    
    from nipype.pipeline.engine import Node, Workflow
    import nipype.interfaces.utility as util
    from nipype.interfaces.dcmstack import DcmStack

    # workflow
    dcmconvert = Workflow(name='dcmconvert')
    
    #inputnode 
    inputnode=Node(util.IdentityInterface(fields=['dicoms',
                                                  'filename']),
                   name='inputnode')
    
    # outputnode                                     
    outputnode=Node(util.IdentityInterface(fields=['nifti']),
                    name='outputnode')
    
    # conversion node
    converter = Node(DcmStack(embed_meta=True),
                     name='converter')
    
    # connections
    dcmconvert.connect([(inputnode, converter, [('dicoms', 'dicom_files'),
                                                ('filename','out_format')]),
                        (converter, outputnode, [('out_file','nifti')])])
    
    return dcmconvert