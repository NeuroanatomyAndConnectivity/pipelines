from nipype.pipeline.engine import Node, Workflow
import nipype.interfaces.utility as util
import nipype.interfaces.ants as ants
import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as nio
import sys
import pandas as pd
from struct_preproc.ants import create_normalize_pipeline
import nipype.interfaces.freesurfer as fs
import os


'''
Calculate transform to MNI with new smaller brainmask
'''

subjects = list(pd.read_csv('/home/raid3/huntenburg/workspace/lsd_data_paper/lsd_preproc.csv', dtype='str')['ID'])
subjects.sort()

scan = 'rest1a'

subjects = [sub for sub in subjects if not os.path.isfile('/nobackup/ilz2/fix_mni/%s/preprocessed/lsd_resting/%s/rest_preprocessed2mni.nii.gz'%(sub,scan))]
print len(subjects)

subjects=['03820']

# for some subjects exclude scans
if scan == 'rest1b':
    subjects.remove('24945')
if scan == 'rest2a':
    subjects.remove('24945')
    subjects.remove('25188')
if scan == 'rest2b':
    subjects.remove('24945')
    subjects.remove('25188')
    subjects.remove('26500')
    subjects.remove('25019')
    subjects.remove('23700')

# local base and output directory
data_dir = '/afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/probands/'
new_data_dir = '/nobackup/ilz2/test_fix/'
base_dir = '/nobackup/ilz2/test_fix/working_dir/'
anat_dir = '/nobackup/ilz2/test_fix/%s/preprocessed/anat/'
func_dir = '/nobackup/ilz2/test_fix/%s/preprocessed/lsd_resting/%s/'

template_2mm ='/usr/share/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz'
template_1mm ='/usr/share/fsl/data/standard/MNI152_T1_1mm_brain.nii.gz'

# workflow
mni = Workflow(name='mni')
mni.base_dir = base_dir
mni.config['execution']['crashdump_dir'] = mni.base_dir + "/crash_files"

# infosource to iterate over subjects
subject_infosource=Node(util.IdentityInterface(fields=['subject_id']),
                        name='subject_infosource')
subject_infosource.iterables=('subject_id', subjects)

# infosource to iterate over scans
# scan_infosource=Node(util.IdentityInterface(fields=['scan']),
#                         name='scan_infosource')
# scan_infosource.iterables=('scan', scans)

# select files
templates={'brain': '{subject_id}/freesurfer/mri/brain.finalsurfs.mgz',
           'func' : '{subject_id}/preprocessed/lsd_resting/%s/rest_preprocessed.nii.gz'%scan
           }
selectfiles = Node(nio.SelectFiles(templates,
                                   base_directory=data_dir),
                   name="selectfiles")

mni.connect([(subject_infosource, selectfiles, [('subject_id', 'subject_id')]),
             #(scan_infosource, selectfiles, [('scan', 'scan')])
             ])

# templates_2={'affine': '{subject_id}/preprocessed/anat/transforms2mni/transform0GenericAffine.mat',
#              'warp': '{subject_id}/preprocessed/anat/transforms2mni/transform1Warp.nii.gz',
#            }
# selectfiles_2 = Node(nio.SelectFiles(templates_2,
#                                    base_directory=new_data_dir),
#                    name="selectfiles_2")
# 
# mni.connect([(subject_infosource, selectfiles_2, [('subject_id', 'subject_id')])])
 
# convert brain to niigz
convert=Node(fs.MRIConvert(out_type='niigz',
                           out_file='T1_brain.nii.gz'),
                   name='convert')
 
mni.connect([(selectfiles, convert, [('brain', 'in_file')])])

# workflow to normalize anatomy to standard space
normalize=create_normalize_pipeline()
normalize.inputs.inputnode.standard = template_1mm
mni.connect([(convert, normalize, [('out_file', 'inputnode.anat')])])

#make filelist
# translist = Node(util.Merge(2),
#                      name='translist')
# mni.connect([(selectfiles_2, translist, [('affine', 'in2'),
#                                        ('warp', 'in1')])])

# project preprocessed time series to mni

applytransform = Node(ants.ApplyTransforms(input_image_type = 3,
                                            output_image='rest_preprocessed2mni.nii.gz',
                                            interpolation = 'BSpline',
                                            invert_transform_flags=[False, False]),
                       name='applytransform')
      
applytransform.inputs.reference_image=template_2mm
mni.connect([(selectfiles, applytransform, [('func', 'input_image')]),
             #(translist, applytransform, [('out', 'transforms')])
             (normalize, applytransform, [('outputnode.anat2std_transforms', 'transforms')])
            ])
  
# tune down image to float
changedt = Node(fsl.ChangeDataType(output_datatype='float',
                                   out_file='rest_preprocessed2mni.nii.gz'),
                name='changedt')
mni.connect([(applytransform, changedt, [('output_image', 'in_file')])])

# make base directory anatomy
def makebase_anat(subject_id, out_dir):
    return out_dir%subject_id

# sink anatomy
anatsink = Node(nio.DataSink(parameterization=False,
                             substitutions=[('transform_Warped', 'T1_brain2mni')]),
                name='anatsink')
 
mni.connect([(subject_infosource, anatsink, [(('subject_id', makebase_anat, anat_dir), 'base_directory')]),
             (convert, anatsink, [('out_file', '@brain')]),
             (normalize, anatsink, [('outputnode.anat2std', '@anat2std'),
                                ('outputnode.anat2std_transforms', 'transforms2mni.@anat2std_transforms'),
                                ('outputnode.std2anat_transforms', 'transforms2mni.@std2anat_transforms')])
             ])


# make base directory functional
def makebase_func(subject_id, scan, out_dir):
    return out_dir%(subject_id, scan)
  
makebasefunc = Node(util.Function(input_names=['subject_id', 'scan', 'out_dir'],
                                  output_names=['basedir'],
                                  function=makebase_func),
                    name='makebase_func')
  
makebasefunc.inputs.out_dir=func_dir
makebasefunc.inputs.scan=scan
mni.connect([(subject_infosource, makebasefunc, [('subject_id', 'subject_id')]),
             #(scan_infosource, makebasefunc, [('scan', 'scan')])
             ])
  
  
#sink functional
funcsink = Node(nio.DataSink(parameterization=False),
                name='funcsink')
  
mni.connect([(makebasefunc, funcsink, [('basedir', 'base_directory')]),
             (changedt, funcsink, [('out_file', '@rest2mni')])
             ])

mni.run(plugin='MultiProc', plugin_args={'n_procs' : 30})