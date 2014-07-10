from nipype import config
config.enable_debug_mode()

import matplotlib
matplotlib.use('Agg')
import os
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.afni as afni

from clustering.similarity import Similarity
from clustering.mask_surface import MaskSurface
from clustering.mask_volume import MaskVolume
from clustering.concat import Concat

from variables import subjects, sessions, workingdir, preprocdir, similaritydir, freesurferdir, similarity_dg_template, similarity_dg_args, fsaverage, hemispheres, similarity_types
from variables import volume_sourcelabels, volume_targetlabels, surface_sourcelabels, surface_targetlabels

def get_wf():
    
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(workingdir,"similarity_pipeline")
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"

##Infosource##    
    subject_id_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_id_infosource")
    subject_id_infosource.iterables = ('subject_id', subjects)

    #session_infosource = pe.Node(util.IdentityInterface(fields=['session']), name="session_infosource")
    #session_infosource.iterables = ('session', sessions)
    
    fs_infosource = pe.Node(util.IdentityInterface(fields=['fs']), name="fs_infosource")
    fs_infosource.iterables = ('fs', fsaverage)

    hemi_infosource = pe.Node(util.  IdentityInterface(fields=['hemi']), name="hemi_infosource")
    hemi_infosource.iterables = ('hemi', hemispheres)

    sim_infosource = pe.Node(util.IdentityInterface(fields=['sim']), name="sim_infosource")
    sim_infosource.iterables = ('sim', similarity_types)

##Datagrabber##
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id','hemi','fs'], outfields=['sxfm','volumedata','regfile','parcfile']), name="datagrabber")
    datagrabber.inputs.base_directory = '/'
    datagrabber.inputs.template = '*'
    datagrabber.inputs.field_template = similarity_dg_template
    datagrabber.inputs.template_args = similarity_dg_args
    datagrabber.inputs.sort_filelist = True

    wf.connect(subject_id_infosource, 'subject_id', datagrabber, 'subject_id')
    #wf.connect(session_infosource, 'session', datagrabber, 'session')
    wf.connect(fs_infosource, 'fs', datagrabber, 'fs')
    wf.connect(hemi_infosource, 'hemi', datagrabber, 'hemi')

##mask surface##
    Smask = pe.Node(MaskSurface(), name = 'surface_mask')
    Smask.inputs.sourcelabels = surface_sourcelabels
    Smask.inputs.targetlabels = surface_targetlabels
    Smask.inputs.freesurferdir = freesurferdir
    wf.connect(hemi_infosource, 'hemi', Smask, 'hemi')
    wf.connect(fs_infosource, 'fs', Smask, 'fs')
    wf.connect(datagrabber, 'sxfm', Smask, 'sxfmout')

##mask volume##
    Vmask = pe.Node(MaskVolume(), name = 'volume_mask')
    Vmask.inputs.vol_source = volume_sourcelabels
    Vmask.inputs.vol_target = volume_targetlabels
    wf.connect(datagrabber, 'volumedata', Vmask, 'preprocessedfile')
    wf.connect(datagrabber, 'regfile', Vmask, 'regfile')
    wf.connect(datagrabber, 'parcfile', Vmask, 'parcfile')

##concatenate data & run similarity##
    concat = pe.JoinNode(Concat(), joinsource="hemi", joinfield=["surface_input"], unique=True, name = 'concat')
    wf.connect(Vmask, 'volume_input_mask', concat, 'volume_input')
    wf.connect(Vmask, 'volume_target_mask', concat, 'volume_target_mask')
    wf.connect(Smask, 'surface_data', concat, 'surface_input')
    wf.connect(Smask, 'surface_mask', concat, 'surface_mask')
    wf.connect(sim_infosource, 'sim', concat, 'sim_type')

##Datasink##
    ds = pe.Node(nio.DataSink(), name="datasink")
    ds.inputs.base_directory = similaritydir
    wf.connect(concat,'simmatrix', ds, 'similarity')
    wf.connect(concat,'maskindex', ds, 'maskindex')
    wf.connect(concat, 'targetmask', ds, 'targetmask')
    wf.write_graph()
    return wf

if __name__ == '__main__':
    wf = get_wf()               
    #wf.run(plugin="CondorDAGMan", plugin_args={"template":"universe = vanilla\nnotification = Error\ngetenv = true\nrequest_memory=4000"})
    #wf.run(plugin="MultiProc", plugin_args={"n_procs":8})
    wf.run(plugin='Linear')
