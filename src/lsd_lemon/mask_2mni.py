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
#subjects = ['03820']


# local base and output directory
afs_dir = '/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/probands/'
base_dir = '/nobackup/ilz2/julia_2mni/working_dir_masks/'
ilz_dir = '/nobackup/ilz2/fix_mni/'
out_dir = '/nobackup/ilz2/julia_2mni/masks'

template ='/usr/share/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz'

# workflow
mni = Workflow(name='mni')
mni.base_dir = base_dir
mni.config['execution']['crashdump_dir'] = mni.base_dir + "/crash_files"

# infosource to iterate over subjects
subject_infosource=Node(util.IdentityInterface(fields=['subject_id']),
                        name='subject_infosource')
subject_infosource.iterables=('subject_id', subjects)

# select files
templates_1={'mask': '{subject_id}/preprocessed/anat/T1_brain_mask.nii.gz',
           #'affine': '{subject_id}/preprocessed/anat/transforms2mni/transform0GenericAffine.mat',
           #'warp': '{subject_id}/preprocessed/anat/transforms2mni/transform1Warp.nii.gz',
           }
selectfiles_1 = Node(nio.SelectFiles(templates_1,
                                   base_directory=afs_dir),
                   name="selectfiles_1")

mni.connect([(subject_infosource, selectfiles_1, [('subject_id', 'subject_id')])])

# select files
templates_2={'affine': '{subject_id}/preprocessed/anat/transforms2mni/transform0GenericAffine.mat',
             'warp': '{subject_id}/preprocessed/anat/transforms2mni/transform1Warp.nii.gz',
           }
selectfiles_2 = Node(nio.SelectFiles(templates_2,
                                   base_directory=ilz_dir),
                   name="selectfiles_2")

mni.connect([(subject_infosource, selectfiles_2, [('subject_id', 'subject_id')])])


# make filelist
translist = Node(util.Merge(2),
                     name='translist')
mni.connect([(selectfiles_2, translist, [('affine', 'in2'),
                                       ('warp', 'in1')])])



def make_name(sub):
    return '%s_brainmask_mni.nii.gz' %(sub)
    
makename = Node(util.Function(input_names=['sub'], 
                              output_names='fname', 
                              function=make_name),
                name='makename')

mni.connect([(subject_infosource, makename, [('subject_id', 'sub')])])

# apply all transforms
applytransform = Node(ants.ApplyTransforms(input_image_type = 3,
                                           #output_image='rest_preprocessed2mni.nii.gz',
                                           interpolation = 'NearestNeighbor',
                                           invert_transform_flags=[False, False]),
                      name='applytransform')
   
applytransform.inputs.reference_image=template
mni.connect([(selectfiles_1, applytransform, [('mask', 'input_image')]),
             (translist, applytransform, [('out', 'transforms')]),
             (makename, applytransform, [('fname', 'output_image')])
             ])


# sink
sink = Node(nio.DataSink(base_directory=out_dir,
                         parameterization=False),
                name='sink')

mni.connect([#(subject_infosource, sink, [(('subject_id', makebase, out_dir), 'base_directory')]),
             (applytransform, sink, [('output_image', '@tsnr2mni')])
             ])

mni.run(plugin='MultiProc', plugin_args={'n_procs' : 10})