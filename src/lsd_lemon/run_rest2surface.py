# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 17:58:59 2015

@author: oligschlager
"""

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
from nipype.interfaces.freesurfer import SampleToSurface
from os import listdir
from os.path import isdir

'''
Script to resample lsd functional  time-series to surface space
----------------------------------------------------------------
picks all subjects that have a lsd rest_preprocessed.nii.gz
'''

'''directories'''
preprocDir = "/scr/ilz2/LEMON_LSD"
freesurferDir = "/scr/ilz2/LEMON_LSD/freesurfer"
workingDir = "/scr/liberia1/LEMON_LSD/vol2surf_workingDir"
sinkDir = "/scr/liberia1/LEMON_LSD"

'''subjects'''
subjects = []
for sub in listdir('/scr/ilz2/LEMON_LSD'):
    if isdir('/scr/ilz2/LEMON_LSD/%s/preprocessed/lsd_resting' %sub):
        subjects.append(sub)

'''workflow'''
if __name__ == '__main__':
    wf = pe.Workflow(name="map_to_surface")
    wf.base_dir = workingDir
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"

    subjects_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subjects_infosource")
    subjects_infosource.iterables = ('subject_id', subjects)

    scan_infosource = pe.Node(util.IdentityInterface(fields=['scan']), name="scan_infosource")
    scan_infosource.iterables = ('scan', ['rest1a', 'rest1b', 'rest2a', 'rest2b'])

    template_infosource = pe.Node(util.IdentityInterface(fields=['fsaverage']), name="template_infosource")
    template_infosource.iterables = ('fsaverage', ['fsaverage4', 'fsaverage5'])

    hemi_infosource = pe.Node(util.IdentityInterface(fields=['hemi']), name="hemi_infosource")
    hemi_infosource.iterables = ('hemi', ['lh', 'rh'])

    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id', 'scan'],
                                          outfields=['resting_lsd']),
                          name="datagrabber")
    datagrabber.inputs.base_directory = preprocDir
    datagrabber.inputs.template = '%s/preprocessed/lsd_resting/%s/rest_preprocessed.nii.gz'
    datagrabber.inputs.template_args['resting_lsd'] = [['subject_id', 'scan']]
    datagrabber.inputs.sort_filelist = True
    datagrabber.inputs.raise_on_empty = False

    vol2surf = pe.Node(SampleToSurface(subjects_dir=freesurferDir,
                                       args='--surfreg sphere.reg',
                                       reg_header=True,
                                       cortex_mask=True,
                                       sampling_method="average",
                                       sampling_range=(0.2, 0.8, 0.1),
                                       sampling_units="frac",
                                       smooth_surf=6.0),
                       name='vol2surf_lsd')


    def gen_out_file(scan, subject_id, hemi, fsaverage):
        return "lsd_%s_%s_preprocessed_%s_%s.mgz" % (scan, subject_id, fsaverage, hemi)
    output_name = pe.Node(util.Function(input_names=['scan', 'subject_id', 'hemi', 'fsaverage'],
                                        output_names=['name'],
                                        function=gen_out_file),
                          name="output_name")

    datasink = pe.Node(nio.DataSink(parameterization=False, base_directory=sinkDir), name='sinker')

    wf.connect([(subjects_infosource, datagrabber, [('subject_id', 'subject_id')]),
                (scan_infosource, datagrabber, [('scan', 'scan')]),
                (subjects_infosource, output_name, [('subject_id', 'subject_id')]),
                (scan_infosource, output_name, [('scan', 'scan')]),
                (template_infosource, output_name, [('fsaverage', 'fsaverage')]),
                (hemi_infosource, output_name, [('hemi', 'hemi')]),
                (subjects_infosource, vol2surf, [('subject_id', 'subject_id')]),
                (hemi_infosource, vol2surf, [('hemi', 'hemi')]),
                (template_infosource, vol2surf, [('fsaverage', 'target_subject')]),
                (datagrabber, vol2surf, [('resting_lsd', 'source_file')]),
                (output_name, vol2surf, [('name', 'out_file')]),
                (vol2surf, datasink, [('out_file', 'LSD_rest_surf')])
                ])

    wf.run(plugin="CondorDAGMan")