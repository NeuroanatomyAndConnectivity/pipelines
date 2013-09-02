import matplotlib
matplotlib.use('Agg')
import os
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio

from consensus import Consensus
from variables import analysis_subjects, analysis_sessions, workingdir, resultsdir, freesurferdir, hemispheres, similarity_types, cluster_types, n_clusters

analysis_subjects = ['9630905']

def get_wf():
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(workingdir,"intercluster_analysis")
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
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id','session','hemi', 'cluster', 'sim', 'n_clusters'], outfields=['all_cluster_types','all_sessions',]), name="datagrabber")
    datagrabber.inputs.base_directory = resultsdir+'clustered/'
    datagrabber.inputs.template = '*%s*/*%s*/*%s*/*%s*/*%s*/*%s*/*'
    datagrabber.inputs.template_args['all_cluster_types'] = [['hemi', 'session','subject_id','*','*','*']]
    datagrabber.inputs.template_args['all_sessions'] = [['hemi', '*','subject_id','sim', 'cluster', 'n_clusters']]
    datagrabber.inputs.sort_filelist = True

    wf.connect(subject_id_infosource, 'subject_id', datagrabber, 'subject_id')
    wf.connect(session_infosource, 'session', datagrabber, 'session')
    wf.connect(hemi_infosource, 'hemi', datagrabber, 'hemi')
    wf.connect(cluster_infosource, 'cluster', datagrabber, 'cluster')
    wf.connect(sim_infosource, 'sim', datagrabber, 'sim')
    wf.connect(n_clusters_infosource, 'n_clusters', datagrabber, 'n_clusters')

##Consensus between cluster_types##
    consensus = pe.Node(Consensus(), name = 'consensus')
    wf.connect(datagrabber, 'all_cluster_types', consensus, 'in_Files')

##Consensus between sessions##
    intersession = pe.Node(Consensus(), name = 'intersession')
    wf.connect(datagrabber, 'all_sessions', intersession, 'in_Files')

##Consensus between subjects?##

##Datasink##
    ds = pe.Node(nio.DataSink(infields=['subject_id','session','hemi', 'cluster', 'sim', 'n_clusters']), name="datasink")
    ds.inputs.base_directory = resultsdir
    ds.inputs.parameterization = False
    wf.connect(consensus, 'out_File', ds, 'compare_cluster_types._subject._session._hemi')
    wf.connect(intersession, 'out_File', ds, 'compare_sessions._subject._hemi._sim._cluster._n_clusters')
    ds.inputs.substitutions = [('_subject', 'subject_id'),
                               ('_session', 'session'),
                               ('_sim', 'sim'),
                               ('_cluster', 'cluster'),
                               ('_n_clusters', 'n_clusters')]
    import pdb
    pdb.set_trace()
    wf.connect(subject_id_infosource, 'subject_id', ds, 'subject_id')
    wf.connect(session_infosource, 'session', ds, 'session')
    wf.connect(hemi_infosource, 'hemi', ds, 'hemi')
    wf.connect(cluster_infosource, 'cluster', ds, 'cluster')
    wf.connect(sim_infosource, 'sim', ds, 'sim')
    wf.connect(n_clusters_infosource, 'n_clusters', ds, 'n_clusters')

    wf.write_graph()
    return wf

if __name__ == '__main__':
    wf = get_wf()               
    #wf.run(plugin="CondorDAGMan", plugin_args={"template":"universe = vanilla\nnotification = Error\ngetenv = true\nrequest_memory=4000"})
    wf.run(plugin="MultiProc", plugin_args={"n_procs":8})
