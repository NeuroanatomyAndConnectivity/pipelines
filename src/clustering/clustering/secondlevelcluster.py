import matplotlib
matplotlib.use('Agg')
import os
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio

from consensus import Consensus
from cluster import Cluster
from variables import analysis_subjects, analysis_sessions, workingdir, resultsdir, freesurferdir, hemispheres, similarity_types, cluster_types, n_clusters


def get_wf():
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(workingdir,"intercluster_analysis")
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"

##Infosource##    
    subject_id_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_id_infosource")
    subject_id_infosource.iterables = ('subject_id', analysis_subjects)

    session_infosource = pe.Node(util.IdentityInterface(fields=['session']), name="session_infosource")
    session_infosource.iterables = ('session', analysis_sessions)
    
    hemi_infosource = pe.Node(util.IdentityInterface(fields=['hemi']), name="hemi_infosource")
    hemi_infosource.iterables = ('hemi', hemispheres)

    sim_infosource = pe.Node(util.IdentityInterface(fields=['sim']), name="sim_infosource")
    sim_infosource.iterables = ('sim', similarity_types)

    cluster_infosource = pe.Node(util.IdentityInterface(fields=['cluster']), name="cluster_infosource")
    cluster_infosource.iterables = ('cluster', cluster_types)

    n_clusters_infosource = pe.Node(util.IdentityInterface(fields=['n_clusters']), name="n_clusters_infosource")
    n_clusters_infosource.iterables = ('n_clusters', n_clusters)

    ##Datagrabber for cluster_type##
    dg_clusters = pe.Node(nio.DataGrabber(infields=['subject_id','session','hemi'], outfields=['all_cluster_types']), name="dg_clusters")
    dg_clusters.inputs.base_directory = resultsdir+'clustered/'
    dg_clusters.inputs.template = '*%s*/*%s*/*%s*/*%s*/*%s*/*%s*/*'
    dg_clusters.inputs.template_args['all_cluster_types'] = [['hemi', 'session','subject_id','*','*','n_clusters']]
    dg_clusters.inputs.sort_filelist = True

    wf.connect(subject_id_infosource, 'subject_id', dg_clusters, 'subject_id')
    wf.connect(session_infosource, 'session', dg_clusters, 'session')
    wf.connect(hemi_infosource, 'hemi', dg_clusters, 'hemi')
    wf.connect(n_clusters_infosource, 'n_clusters', dg_clusters, 'n_clusters')

##Cluster the Consensus Matrix##
    consensus_cluster = pe.Node(Cluster(), name = 'consensus')
    wf.connect(intercluster, 'consensus_mat', consensus_cluster, 'in_File')

##Datasink
    ds = pe.Node(nio.DataSink(), name="datasink")
    ds.inputs.base_directory = resultsdir
    wf.connect(consensus_cluster, 'out_File', ds, 'consensus_clustered')

    wf.write_graph()
    return wf

if __name__ == '__main__':
    wf = get_wf()               
    #wf.run(plugin="CondorDAGMan", plugin_args={"template":"universe = vanilla\nnotification = Error\ngetenv = true\nrequest_memory=4000"})
    wf.run(plugin="MultiProc", plugin_args={"n_procs":8})
