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
from cluster import Cluster
from similarity import Similarity
from mask import Mask
from variables import analysis_subjects, analysis_sessions, workingdir, resultsdir,  freesurferdir, hemispheres, similarity_types, cluster_types, n_clusters

os.environ['SUBJECTS_DIR'] = freesurferdir

def get_wf():
    
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(workingdir,"cluster_analysis")
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"

##Infosource##    
    subject_id_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_id_infosource")
    subject_id_infosource.iterables = ('subject_id', analysis_subjects)

    session_infosource = pe.Node(util.IdentityInterface(fields=['session']), name="session_infosource")
    session_infosource.iterables = ('session', analysis_sessions)
    
    hemi_infosource = pe.Node(util.  IdentityInterface(fields=['hemi']), name="hemi_infosource")
    hemi_infosource.iterables = ('hemi', hemispheres)

    sim_infosource = pe.Node(util.IdentityInterface(fields=['sim']), name="sim_infosource")
    sim_infosource.iterables = ('sim', similarity_types)

    cluster_infosource = pe.Node(util.IdentityInterface(fields=['cluster']), name="cluster_infosource")
    cluster_infosource.iterables = ('cluster', cluster_types)

    n_clusters_infosource = pe.Node(util.IdentityInterface(fields=['n_clusters']), name="n_clusters_infosource")
    n_clusters_infosource.iterables = ('n_clusters', n_clusters)

##Datagrabber##
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id','session','hemi'], outfields=['sxfmout']), name="datagrabber")
    datagrabber.inputs.base_directory = resultsdir+'sxfmout/'
    datagrabber.inputs.template = '*%s/*%s/%s/*%s/%s'
    datagrabber.inputs.template_args['sxfmout'] = [['session','subject_id','*','hemi', '*.nii']]
    datagrabber.inputs.sort_filelist = True

    wf.connect(subject_id_infosource, 'subject_id', datagrabber, 'subject_id')
    wf.connect(session_infosource, 'session', datagrabber, 'session')
    wf.connect(hemi_infosource, 'hemi', datagrabber, 'hemi')

##mask##
    mask = pe.Node(Mask(), name = 'mask')
    wf.connect(hemi_infosource, 'hemi', mask, 'hemi')
    wf.connect(datagrabber, 'sxfmout', mask, 'sxfmout')

##similaritymatrix##
    simmatrix = pe.Node(util.Function(input_names=['in_file','sim','mask'], output_names=['out_file'], function=Similarity), name='simmatrix')
    wf.connect(mask, 'mask_volume', simmatrix, 'mask')
    wf.connect(datagrabber, 'sxfmout', simmatrix, 'in_file')
    wf.connect(sim_infosource, 'sim', simmatrix, 'sim')

##clustering##
    clustering = pe.Node(Cluster(), name = 'clustering')
    wf.connect(datagrabber, 'sxfmout', clustering, 'sxfmout')
    wf.connect(hemi_infosource, 'hemi', clustering, 'hemi')
    wf.connect(cluster_infosource, 'cluster', clustering, 'cluster_type')
    wf.connect(n_clusters_infosource, 'n_clusters', clustering, 'n_clusters')
    wf.connect(simmatrix, 'out_file', clustering, 'volume')

##Datasink##
    ds = pe.Node(nio.DataSink(), name="datasink")
    ds.inputs.base_directory = resultsdir
    wf.connect(simmatrix,'out_file', ds, 'similarity')
    wf.connect(clustering, 'clustered_volume', ds, 'clustered')
    wf.write_graph()
    return wf

if __name__ == '__main__':
    wf = get_wf()               
    wf.run(plugin="CondorDAGMan", plugin_args={"template":"universe = vanilla\nnotification = Error\ngetenv = true\nrequest_memory=4000"})
    #wf.run(plugin="MultiProc", plugin_args={"n_procs":8})
