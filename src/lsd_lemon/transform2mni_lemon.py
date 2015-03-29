from nipype.pipeline.engine import Node, Workflow
import nipype.interfaces.utility as util
import nipype.interfaces.ants as ants
import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as nio
import sys


'''
Project preprocessed lemon resting state from 
individual structural to MNI152 2mm space
'''

subject_list= sys.argv[1]

with open(subject_list, 'r') as f:
    subjects = [line.strip() for line in f]


# local base and output directory
data_dir = '/scr/ilz2/LEMON_LSD/'
base_dir = '/scr/ilz2/LEMON_LSD/working_dir_lemon_mni/'
out_dir = '/scr/ilz2/LEMON_LSD/%s/preprocessed/lemon_resting/'

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
templates={'rest': '{subject_id}/preprocessed/lemon_resting/rest_preprocessed.nii.gz',
           'affine': '{subject_id}/preprocessed/anat/transforms2mni/transform0GenericAffine.mat',
           'warp': '{subject_id}/preprocessed/anat/transforms2mni/transform1Warp.nii.gz',
           }
selectfiles = Node(nio.SelectFiles(templates,
                                   base_directory=data_dir),
                   name="selectfiles")

mni.connect([(subject_infosource, selectfiles, [('subject_id', 'subject_id')])])

# make filelist
translist = Node(util.Merge(2),
                     name='translist')
mni.connect([(selectfiles, translist, [('affine', 'in2'),
                                       ('warp', 'in1')])])


# apply all transforms
applytransform = Node(ants.ApplyTransforms(input_image_type = 3,
                                           #output_image='rest_preprocessed2mni.nii.gz',
                                           interpolation = 'BSpline',
                                           invert_transform_flags=[False, False]),
                      name='applytransform')
   
applytransform.inputs.reference_image=template
applytransform.plugin_args={'submit_specs': 'request_memory = 30000'}
mni.connect([(selectfiles, applytransform, [('rest', 'input_image')]),
             (translist, applytransform, [('out', 'transforms')])
             ])

# tune down image to float
changedt = Node(fsl.ChangeDataType(output_datatype='float',
                                   out_file='rest_preprocessed2mni.nii.gz'),
                name='changedt')
changedt.plugin_args={'submit_specs': 'request_memory = 30000'}
mni.connect([(applytransform, changedt, [('output_image', 'in_file')])])


# make base directory
def makebase(subject_id, out_dir):
    return out_dir%subject_id

# sink
sink = Node(nio.DataSink(base_directory=out_dir,
                         parameterization=False),
                name='sink')

mni.connect([(subject_infosource, sink, [(('subject_id', makebase, out_dir), 'base_directory')]),
             (changedt, sink, [('out_file', '@rest2mni')])
             ])

mni.run()