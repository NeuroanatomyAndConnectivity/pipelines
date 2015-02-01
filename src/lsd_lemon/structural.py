from nipype.pipeline.engine import Node, Workflow
import nipype.interfaces.io as nio
from struct_preproc.mp2rage import create_mp2rage_pipeline
from struct_preproc.reconall import create_reconall_pipeline
from struct_preproc.mgzconvert import create_mgzconvert_pipeline
from struct_preproc.ants import create_normalize_pipeline

'''
Main workflow for preprocessing of mp2rage data
===============================================
Uses file structure set up by conversion
'''

def create_structural(subject, working_dir, data_dir, freesurfer_dir, out_dir,
                standard_brain):
    
    # main workflow
    struct_preproc = Workflow(name='mp2rage_preproc')
    struct_preproc.base_dir = working_dir
    struct_preproc.config['execution']['crashdump_dir'] = struct_preproc.base_dir + "/crash_files"
    
    # select files
    templates={'inv2': 'nifti/mp2rage/inv2.nii.gz',
               't1map': 'nifti/mp2rage/t1map.nii.gz',
               'uni': 'nifti/mp2rage/uni.nii.gz'}
    selectfiles = Node(nio.SelectFiles(templates,
                                       base_directory=data_dir),
                       name="selectfiles")
    
    # workflow for mp2rage background masking
    mp2rage=create_mp2rage_pipeline()
    
    # workflow to run freesurfer reconall
    reconall=create_reconall_pipeline()
    reconall.inputs.inputnode.fs_subjects_dir=freesurfer_dir
    reconall.inputs.inputnode.fs_subject_id=subject
    
    # workflow to get brain, head and wmseg from freesurfer and convert to nifti
    mgzconvert=create_mgzconvert_pipeline()
    
    # workflow to normalize anatomy to standard space
    normalize=create_normalize_pipeline()
    normalize.inputs.inputnode.standard = standard_brain
    
    #sink to store files
    sink = Node(nio.DataSink(base_directory=out_dir,
                             parameterization=False,
                             substitutions=[('outStripped', 'uni_stripped'),
                                            ('outMasked2', 'uni_masked'),
                                            ('outSignal2', 'background_mask'),
                                            ('outOriginal', 'uni_reoriented'),
                                            ('outMask', 'skullstrip_mask'),
                                            ('transform_Warped', 'T1_brain2mni')]),
                 name='sink')
    
    
    # connections
    struct_preproc.connect([(selectfiles, mp2rage, [('inv2', 'inputnode.inv2'),
                                                    ('t1map', 'inputnode.t1map'),
                                                    ('uni', 'inputnode.uni')]),
                            (mp2rage, reconall, [('outputnode.uni_masked', 'inputnode.anat')]),
                            (reconall, mgzconvert, [('outputnode.fs_subject_id', 'inputnode.fs_subject_id'),
                                                    ('outputnode.fs_subjects_dir', 'inputnode.fs_subjects_dir')]),
                            (mgzconvert, normalize, [('outputnode.anat_brain', 'inputnode.anat')]),
                            #(mp2rage, sink, [('outputnode.uni_masked', 'preprocessed.mp2rage.background_masking.@uni_masked'),
                            #                 ('outputnode.background_mask', 'preprocessed.mp2rage.background_masking.@background_mask')
                            #                 ]),
                            (mgzconvert, sink, [('outputnode.anat_head', 'preprocessed.anat.@head'),
                                                ('outputnode.anat_brain', 'preprocessed.anat.@brain'),
                                                ('outputnode.brain_mask', 'preprocessed.anat.@brain_mask'),
                                                ('outputnode.wmedge', 'preprocessed.anat.@wmedge'),
                                                #('outputnode.wmseg', 'preprocessed.mp2rage.brain_extraction.@wmseg')
                                                ]),
                            (normalize, sink, [('outputnode.anat2std', 'preprocessed.anat.@anat2std'),
                                               ('outputnode.anat2std_transforms', 'preprocessed.anat.transforms2mni.@anat2std_transforms'),
                                               ('outputnode.std2anat_transforms', 'preprocessed.anat.transforms2mni.@std2anat_transforms')])
                            ])
    #struct_preproc.write_graph(dotfilename='struct_preproc.dot', graph2use='colored', format='pdf', simple_form=True)
    struct_preproc.run()
    #struct_preproc.run(plugin='CondorDAGMan')
    #struct_preproc.run(plugin='MultiProc')
