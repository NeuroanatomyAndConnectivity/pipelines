from nipype.pipeline.engine import Node, Workflow
import nipype.interfaces.utility as util
import nipype.interfaces.ants as ants
import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as nio
import sys
import pandas as pd


'''
Project tsnr / brainmask from 
individual structural to MNI152 2mm space
'''

#subject_list= sys.argv[1]

#with open(subject_list, 'r') as f:
#    subjects = [line.strip() for line in f]

subjects = list(pd.read_csv('/home/raid3/huntenburg/workspace/lsd_data_paper/lsd_preproc.csv', dtype='str')['ID'])
subjects.sort()

subjects.remove('24945')
subjects.remove('25188')
subjects.remove('26500')
subjects.remove('25019')
subjects.remove('23700')
scans = ['rest1a', 'rest1b', 'rest2a', 'rest2b']

# for some subjects exclude scans
#subjects = ['24945']
#scans = ['rest1a']

#subjects = ['25188']
#scans = ['rest1a', 'rest1b']

#subjects = ['26500', '25019', '23700']
#scans = ['rest1a', 'rest1b', 'rest2a']




# local base and output directory
afs_dir = '/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/probands/'
base_dir = '/nobackup/ilz2/julia_2mni/working_dir/'
out_dir = '/nobackup/ilz2/julia_2mni/tsnr/'
ilz_dir =  '/nobackup/ilz2/fix_mni/'

template ='/usr/share/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz'

# workflow
mni = Workflow(name='mni')
mni.base_dir = base_dir
mni.config['execution']['crashdump_dir'] = mni.base_dir + "/crash_files"

# infosource to iterate over subjects
subject_infosource=Node(util.IdentityInterface(fields=['subject_id']),
                        name='subject_infosource')
subject_infosource.iterables=('subject_id', subjects)

# infosource to iterate over scans
scan_infosource=Node(util.IdentityInterface(fields=['scan']),
                        name='scan_infosource')
scan_infosource.iterables=('scan', scans)

# select files
templates_1={'tsnr': '{subject_id}/preprocessed/lsd_resting/{scan}/realign/*tsnr.nii.gz',
           'anat_resamp' : '{subject_id}/preprocessed/lsd_resting/{scan}/coregister/T1_resampled.nii.gz',
           #'affine': '{subject_id}/preprocessed/anat/transforms2mni/transform0GenericAffine.mat',
           #'warp': '{subject_id}/preprocessed/anat/transforms2mni/transform1Warp.nii.gz',
           'func_warp' : '{subject_id}/preprocessed/lsd_resting/{scan}/coregister/transforms2anat/fullwarpfield.nii.gz'
           }
selectfiles_1 = Node(nio.SelectFiles(templates_1,
                                   base_directory=afs_dir),
                   name="selectfiles_1")

mni.connect([(subject_infosource, selectfiles_1, [('subject_id', 'subject_id')]),
             (scan_infosource, selectfiles_1, [('scan', 'scan')])])

# select files
templates_2={ 'affine': '{subject_id}/preprocessed/anat/transforms2mni/transform0GenericAffine.mat',
             'warp': '{subject_id}/preprocessed/anat/transforms2mni/transform1Warp.nii.gz',
           }
selectfiles_2 = Node(nio.SelectFiles(templates_2,
                                   base_directory=ilz_dir),
                   name="selectfiles_2")

mni.connect([(subject_infosource, selectfiles_2, [('subject_id', 'subject_id')])])


# applymoco premat and fullwarpfield
applywarp = Node(fsl.ApplyWarp(interp='spline',
                                         relwarp=True,
                                         datatype='float'),
                    name='applywarp') 

       
mni.connect([(selectfiles_1, applywarp, [('tsnr', 'in_file'),
                                       ('func_warp', 'field_file'), 
                                       ('anat_resamp', 'ref_file')])
             ])

# make filelist
translist = Node(util.Merge(2),
                     name='translist')
mni.connect([(selectfiles_2, translist, [('affine', 'in2'),
                                       ('warp', 'in1')])])



def make_name(sub, scan):
    return '%s_%s_tsnr_mni.nii.gz' %(sub, scan)
    
makename = Node(util.Function(input_names=['sub', 'scan'], 
                              output_names='fname', 
                              function=make_name),
                name='makename')

mni.connect([(subject_infosource, makename, [('subject_id', 'sub')]),
             (scan_infosource, makename, [('scan', 'scan')])])

# apply all transforms
applytransform = Node(ants.ApplyTransforms(input_image_type = 3,
                                           #output_image='rest_preprocessed2mni.nii.gz',
                                           interpolation = 'BSpline',
                                           invert_transform_flags=[False, False]),
                      name='applytransform')
   
applytransform.inputs.reference_image=template
mni.connect([(applywarp, applytransform, [('out_file', 'input_image')]),
             (translist, applytransform, [('out', 'transforms')]),
             (makename, applytransform, [('fname', 'output_image')])
             ])

# tune down image to float
#changedt = Node(fsl.ChangeDataType(output_datatype='float',
#                                   out_file='tsnr2mni.nii.gz'),
#                name='changedt')
#changedt.plugin_args={'submit_specs': 'request_memory = 30000'}
#mni.connect([(applytransform, changedt, [('output_image', 'in_file')])])


# make base directory
# def makebase(subject_id, out_dir):
#     return out_dir%subject_id

# sink
sink = Node(nio.DataSink(base_directory=out_dir,
                         parameterization=False),
                name='sink')

mni.connect([#(subject_infosource, sink, [(('subject_id', makebase, out_dir), 'base_directory')]),
             (applytransform, sink, [('output_image', '@tsnr2mni')])
             ])

mni.run(plugin='MultiProc', plugin_args={'n_procs' : 40})