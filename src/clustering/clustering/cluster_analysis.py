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
from cluster import Cluster
from similarity import Similarity
from mask_surface import MaskSurface
from mask_volume import MaskVolume
from concat import Concat
from variables import subjects, sessions, workingdir, clusterdir, freesurferdir, hemispheres, similarity_types, cluster_types, n_clusters

def get_wf():
    
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(workingdir,"cluster_analysis")
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"

##Infosource##    
    subject_id_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_id_infosource")
    subject_id_infosource.iterables = ('subject_id', subjects)

    session_infosource = pe.Node(util.IdentityInterface(fields=['session']), name="session_infosource")
    session_infosource.iterables = ('session', sessions)
    
    hemi_infosource = pe.Node(util.  IdentityInterface(fields=['hemi']), name="hemi_infosource")
    hemi_infosource.iterables = ('hemi', hemispheres)

    sim_infosource = pe.Node(util.IdentityInterface(fields=['sim']), name="sim_infosource")
    sim_infosource.iterables = ('sim', similarity_types)

    cluster_infosource = pe.Node(util.IdentityInterface(fields=['cluster']), name="cluster_infosource")
    cluster_infosource.iterables = ('cluster', cluster_types)

    n_clusters_infosource = pe.Node(util.IdentityInterface(fields=['n_clusters']), name="n_clusters_infosource")
    n_clusters_infosource.iterables = ('n_clusters', n_clusters)

##Datagrabber##
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id','session','hemi'], outfields=['sxfm','volumedata','regfile','parcfile']), name="datagrabber")
    datagrabber.inputs.base_directory = workingdir
    datagrabber.inputs.template = '*'
    datagrabber.inputs.field_template = dict(sxfm='preprocResults/sxfmout/*%s/*%s/*/*%s/*.nii',
                                            volumedata='preprocResults/preprocessed_resting/*%s/*%s/*/*/*.nii.gz',
                                            regfile='preprocResults/func2anat_transform/*%s/*%s/*/FREESURFER.mat',
                                            parcfile='freesurfer/*%s/FREESURFER/mri/aparc.a2009s+aseg.mgz',)
    datagrabber.inputs.template_args = dict(sxfm=[['session','subject_id', 'hemi']],
                                           volumedata=[['session','subject_id']],
                                           regfile=[['session','subject_id']],
                                           parcfile=[['subject_id']])
    datagrabber.inputs.sort_filelist = True

##Datagrabber##
#    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id','session','hemi'], outfields=['sxfm','volumedata','regfile','parcfile']), name="datagrabber")
#    datagrabber.inputs.base_directory = workingdir
#    datagrabber.inputs.template = '%s*%s/*%s*%s%s%s'
#    datagrabber.inputs.template_args['sxfm'] = [['preprocResults/sxfmout/','session','subject_id','/*/*','hemi','/*.nii']]
#    datagrabber.inputs.template_args['volumedata'] = [['preprocResults/preprocessed_resting/','session','subject_id','/*/*','/*.nii.gz','']]
#    datagrabber.inputs.template_args['regfile'] = [['preprocResults/func2anat_transform/','session','subject_id','/*/','FREESURFER.mat','']]
#    datagrabber.inputs.template_args['parcfile'] = [['freesurfer/','subject_id','FREESURFER','/mri','/aparc.a2009s+aseg.mgz','']]
#    datagrabber.inputs.sort_filelist = True

    wf.connect(subject_id_infosource, 'subject_id', datagrabber, 'subject_id')
    wf.connect(session_infosource, 'session', datagrabber, 'session')
    wf.connect(hemi_infosource, 'hemi', datagrabber, 'hemi')

##mask surface##
    Smask = pe.Node(MaskSurface(), name = 'surface_mask')
    wf.connect(hemi_infosource, 'hemi', Smask, 'hemi')
    wf.connect(datagrabber, 'sxfm', Smask, 'sxfmout')

##mask volume##
    Vmask = pe.Node(MaskVolume(), name = 'volume_mask')
    wf.connect(datagrabber, 'volumedata', Vmask, 'preprocessedfile')
    wf.connect(datagrabber, 'regfile', Vmask, 'regfile')
    wf.connect(datagrabber, 'parcfile', Vmask, 'parcfile')

##concatenate data & run similarity##
    concat = pe.Node(Concat(), name = 'concat')
    wf.connect(Vmask, 'volume_input_mask', concat, 'volume_input')
    wf.connect(Vmask, 'volume_target_mask', concat, 'volume_target_mask')
    wf.connect(Smask, 'surface_data', concat, 'surface_input')
    wf.connect(Smask, 'surface_mask', concat, 'surface_mask')
    wf.connect(sim_infosource, 'sim', concat, 'sim_type')

##clustering##
    clustering = pe.Node(Cluster(), name = 'clustering')
    wf.connect(hemi_infosource, 'hemi', clustering, 'hemi')
    wf.connect(cluster_infosource, 'cluster', clustering, 'cluster_type')
    wf.connect(n_clusters_infosource, 'n_clusters', clustering, 'n_clusters')
    wf.connect(concat, 'simmatrix', clustering, 'in_File')

##Datasink##
    ds = pe.Node(nio.DataSink(), name="datasink")
    ds.inputs.base_directory = clusterdir
    wf.connect(concat,'simmatrix', ds, 'similarity')
    wf.connect(concat,'maskindex', ds, 'maskindex')
    wf.connect(clustering, 'out_File', ds, 'clustered')
    wf.write_graph()
    return wf

if __name__ == '__main__':
    wf = get_wf()               
    #wf.run(plugin="CondorDAGMan", plugin_args={"template":"universe = vanilla\nnotification = Error\ngetenv = true\nrequest_memory=4000"})
    #wf.run(plugin="MultiProc", plugin_args={"n_procs":8})
    wf.run(plugin='Linear')
