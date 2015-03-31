# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 17:58:59 2015

@author: oligschlager
"""

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
from nipype.interfaces.freesurfer import SampleToSurface



subjects = ['26917']

workingDir = "/scr/liberia1/lemon_lsd_surface/working_dir"
preprocDir = "/scr/ilz2/LEMON_LSD"
freesurferDir = "/scr/ilz2/LEMON_LSD/freesurfer"


if __name__ == '__main__':
    wf = pe.Workflow(name="map_to_surface")
    wf.base_dir = workingDir
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
    
    
    
    subjects_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subjects_infosource")
    subjects_infosource.iterables = ('subject_id', subjects)
                            
    run_infosource = pe.Node(util.IdentityInterface(fields=['run']), name="run_infosource")
    run_infosource.iterables = ('run', ['rest1a', 'rest1b', 'rest2a', 'rest2b'])
    
    hemi_infosource = pe.Node(util.IdentityInterface(fields=['hemi']), name="hemi_infosource")
    hemi_infosource.iterables = ('hemi', ['lh', 'rh'])
    
    
    #datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id', 'run'], 
                                          #outfields=['resting_lsd'],
                                          #base_directory = preprocDir,
                                          #template = '%s/preprocessed/lsd_resting/%s/rest_preprocessed.nii.gz',
                                          #template_args['resting_lsd'] = [['subject_id', 'run']],
                                          #sort_filelist = True,
                                          #raise_on_empty = False), 
                                          #name="datagrabber")                                     
                                          
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id', 'run'], outfields=['resting_lsd']), name="datagrabber")
    datagrabber.inputs.base_directory = preprocDir
    datagrabber.inputs.template = '%s/preprocessed/lsd_resting/%s/rest_preprocessed.nii.gz'
    datagrabber.inputs.template_args['resting_lsd'] = [['subject_id', 'run']]
    datagrabber.inputs.sort_filelist = True
    datagrabber.inputs.raise_on_empty = False
                                                                                         
                                         
    
    vol2surf = pe.Node(SampleToSurface(subjects_dir = freesurferDir,
                                               target_subject = 'fsaverage5',
                                               args = '--surfreg sphere.reg',
                                               reg_header = True,     
                                               cortex_mask = True,
                                               sampling_method = "average",
                                               sampling_range = (0.2, 0.8, 0.1), 
                                               sampling_units = "frac", 
                                               smooth_surf = 6.0), 
                                               name='vol2surf_lsd')                                               
       
    datasink = pe.Node(nio.DataSink(base_directory='/scr/liberia1/lemon_lsd_surface/results_test'), name = 'sinker')
    
    
    
    wf.connect(subjects_infosource, 'subject_id', datagrabber, 'subject_id')
    wf.connect(run_infosource, 'run', datagrabber, 'run')
    wf.connect(datagrabber, 'resting_lsd', vol2surf, 'source_file')
    wf.connect(subjects_infosource, 'subject_id', vol2surf, 'subject_id')
    wf.connect(hemi_infosource, 'hemi', vol2surf, 'hemi')
    wf.connect(vol2surf, 'out_file', datasink, 'test')
                                           
       
    wf.run()



    '''
    mri_vol2surf --surfreg sphere.reg --cortex --hemi lh 
    --o /scr/liberia1/lemon_lsd_surface/working_dir/map_to_surface/_run_rest2a/_subject_id_26917/_hemi_lh/vol2surf_lsd/lh.rest_preprocessed.mgz 
    --regheader 26917 --projfrac-avg 0.200 0.800 0.100 
    --surf-fwhm 6.000 --mov /scr/ilz2/LEMON_LSD/26917/preprocessed/lsd_resting/rest2a/rest_preprocessed.nii.gz --trgsubject fsaverage5'
    '''

    #interp_method = "trilinear",  or 'nearest'                                  
    #sampling_method = "average",
    #sampling_range = (0.2, 0.8, 0.1), 
    #sampling_units = "frac", 

