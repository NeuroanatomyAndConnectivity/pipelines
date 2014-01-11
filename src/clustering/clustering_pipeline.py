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

from clustering.cluster import Cluster
from clustering.similarity import Similarity
from clustering.mask_surface import MaskSurface
from clustering.mask_volume import MaskVolume
from clustering.concat import Concat
from clustering.cluster_map import ClusterMap
from clustering.utils import get_subjects_from

from variables import subjects, sessions, workingdir, similaritydir, clusterdir, freesurferdir, clustering_dg_template, clustering_dg_args, hemispheres, similarity_types, cluster_types, n_clusters, epsilon

def get_wf():
    
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(workingdir,"clustering_pipeline")
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"

##Infosource##    
    subject_id_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_id_infosource")
    subject_id_infosource.iterables = ('subject_id', subjects)

    #session_infosource = pe.Node(util.IdentityInterface(fields=['session']), name="session_infosource")
    #session_infosource.iterables = ('session', sessions)
    
    hemi_infosource = pe.Node(util.  IdentityInterface(fields=['hemi']), name="hemi_infosource")
    hemi_infosource.iterables = ('hemi', hemispheres)

    sim_infosource = pe.Node(util.IdentityInterface(fields=['sim']), name="sim_infosource")
    sim_infosource.iterables = ('sim', similarity_types)

    cluster_infosource = pe.Node(util.IdentityInterface(fields=['cluster']), name="cluster_infosource")
    cluster_infosource.iterables = ('cluster', cluster_types)

    n_clusters_infosource = pe.Node(util.IdentityInterface(fields=['n_clusters']), name="n_clusters_infosource")
    n_clusters_infosource.iterables = ('n_clusters', n_clusters)

##Datagrabber##
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id','hemi','sim'], outfields=['simmatrix','maskindex','targetmask']), name="datagrabber")
    datagrabber.inputs.base_directory = '/'
    datagrabber.inputs.template = '*'
    datagrabber.inputs.field_template = clustering_dg_template
    datagrabber.inputs.template_args = clustering_dg_args
    datagrabber.inputs.sort_filelist = True

    wf.connect(subject_id_infosource, 'subject_id', datagrabber, 'subject_id')
    #wf.connect(session_infosource, 'session', datagrabber, 'session')
    wf.connect(hemi_infosource, 'hemi', datagrabber, 'hemi')
    wf.connect(sim_infosource, 'sim', datagrabber, 'sim')

##clustering##
    clustering = pe.Node(Cluster(), name = 'clustering')
    clustering.inputs.epsilon = epsilon
    wf.connect(hemi_infosource, 'hemi', clustering, 'hemi')
    wf.connect(cluster_infosource, 'cluster', clustering, 'cluster_type')
    wf.connect(n_clusters_infosource, 'n_clusters', clustering, 'n_clusters')
    wf.connect(datagrabber, 'simmatrix', clustering, 'in_File')

##reinflate to surface indices##
    clustermap = pe.Node(ClusterMap(), name = 'clustermap')
    wf.connect(clustering, 'out_File', clustermap, 'clusteredfile')
    wf.connect(datagrabber, 'maskindex', clustermap, 'indicesfile')
    wf.connect(datagrabber, 'targetmask', clustermap, 'maskfile')    

##Datasink##
    ds = pe.Node(nio.DataSink(), name="datasink")
    ds.inputs.base_directory = clusterdir
    wf.connect(clustermap, 'clustermapfile', ds, 'clustered')
    wf.write_graph()
    return wf

if __name__ == '__main__':
    wf = get_wf()               
    #wf.run(plugin="CondorDAGMan", plugin_args={"template":"universe = vanilla\nnotification = Error\ngetenv = true\nrequest_memory=4000"})
    wf.run(plugin="MultiProc", plugin_args={"n_procs":8})
    #wf.run(plugin='Linear')
