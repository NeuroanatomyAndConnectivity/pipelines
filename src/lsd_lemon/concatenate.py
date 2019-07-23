from nipype.pipeline.engine import Node, Workflow
import nipype.interfaces.utility as util
import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as nio
import sys


'''
Concatenating all 4 lsd runs of a subject
==========================================
'''

subject_id=sys.argv[1]

# local base and output directory
data_dir = '/scr/ilz2/LEMON_LSD/'+subject_id+'/preprocessed/lsd_resting/'
base_dir = '/scr/ilz2/LEMON_LSD/working_dir/'+subject_id+'/'
out_dir = '/scr/ilz2/LEMON_LSD/'+subject_id+'/preprocessed/lsd_resting/'

# workflow
concat = Workflow(name='concat')
concat.base_dir = base_dir
concat.config['execution']['crashdump_dir'] = concat.base_dir + "/crash_files"

# select files
templates={'rest1a': 'rest1a/rest_preprocessed.nii.gz',
           'rest1b': 'rest1b/rest_preprocessed.nii.gz',
           'rest2a': 'rest2a/rest_preprocessed.nii.gz',
           'rest2b': 'rest2b/rest_preprocessed.nii.gz',
           }
selectfiles = Node(nio.SelectFiles(templates,
                                   base_directory=data_dir),
                   name="selectfiles")

# make filelist
def makelist(in1, in2, in3, in4):
    return [in1, in2, in3, in4]

make_list = Node(util.Function(input_names=['in1', 'in2', 'in3', 'in4'],
                               output_names=['file_list'],
                               function=makelist),
                               name='make_list')

# concatenate scans
concatenate=Node(fsl.Merge(dimension='t',
                           merged_file='rest_concatenated.nii.gz'),
                 name='concatenate')
concatenate.plugin_args={'submit_specs': 'request_memory = 20000'}

# sink
sink = Node(nio.DataSink(base_directory=out_dir,
                         parameterization=False),
                name='sink')

concat.connect([(selectfiles, make_list, [('rest1a', 'in1'),
                                          ('rest1b', 'in2'),
                                          ('rest2a', 'in3'),
                                          ('rest2b', 'in4')]),
                (make_list, concatenate, [('file_list', 'in_files')]),
                (concatenate, sink, [('merged_file', '@rest_concat')])
                ])

concat.run()
#concat.run(plugin='CondorDAGMan')