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

from variables import subjects, sessions, workingdir, preprocdir, clusterdir, freesurferdir, hemispheres, similarity_types, cluster_types, n_clusters, epsilon
from variables import volume_sourcelabels, volume_targetlabels, lhsource, rhsource, lhvertices, rhvertices

subjects= ['0198985','0188854','0186697','0168413','0164900','0162704','0157947','0139212','0136303','0133436']

def get_wf():
    
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(workingdir,"cluster_analysis")
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
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id','hemi'], outfields=['sxfm','volumedata','regfile','parcfile']), name="datagrabber")
    datagrabber.inputs.base_directory = '/'
    datagrabber.inputs.template = '*'
    datagrabber.inputs.field_template = dict(sxfm=os.path.join(preprocdir,'aimivolumes/sxfmout/*%s/_fwhm_0/*%s/*/*.nii'),
                                            volumedata=os.path.join(preprocdir,'aimivolumes/preprocessed_resting/*%s/_fwhm_0/*/*/*.nii.gz'),
                                            regfile=os.path.join(preprocdir,'aimivolumes/func2anat_transform/*%s/*/*%s.mat'),
                                            parcfile=os.path.join(freesurferdir,'*%s/mri/aparc.a2009s+aseg.mgz'),)
    datagrabber.inputs.template_args = dict(sxfm=[['subject_id', 'hemi']],
                                           volumedata=[['subject_id']],
                                           regfile=[['subject_id','subject_id']],
                                           parcfile=[['subject_id']])
    datagrabber.inputs.sort_filelist = True

    wf.connect(subject_id_infosource, 'subject_id', datagrabber, 'subject_id')
    #wf.connect(session_infosource, 'session', datagrabber, 'session')
    wf.connect(hemi_infosource, 'hemi', datagrabber, 'hemi')

##mask surface##
    Smask = pe.Node(MaskSurface(), name = 'surface_mask')
    Smask.inputs.lhvertices = lhvertices
    Smask.inputs.rhvertices = rhvertices
    Smask.inputs.lhsource = lhsource
    Smask.inputs.rhsource = rhsource
    wf.connect(hemi_infosource, 'hemi', Smask, 'hemi')
    wf.connect(datagrabber, 'sxfm', Smask, 'sxfmout')

##mask volume##
    Vmask = pe.Node(MaskVolume(), name = 'volume_mask')
    Vmask.inputs.vol_source = volume_sourcelabels
    Vmask.inputs.vol_target = volume_targetlabels
    wf.connect(datagrabber, 'volumedata', Vmask, 'preprocessedfile')
    wf.connect(datagrabber, 'regfile', Vmask, 'regfile')
    wf.connect(datagrabber, 'parcfile', Vmask, 'parcfile')

##concatenate data & run similarity##
    concat = pe.Node(Concat(), name = 'concat', overwrite=True)
    wf.connect(Vmask, 'volume_input_mask', concat, 'volume_input')
    wf.connect(Vmask, 'volume_target_mask', concat, 'volume_target_mask')
    wf.connect(Smask, 'surface_data', concat, 'surface_input')
    wf.connect(Smask, 'surface_mask', concat, 'surface_mask')
    wf.connect(sim_infosource, 'sim', concat, 'sim_type')

##clustering##
    clustering = pe.Node(Cluster(), name = 'clustering')
    clustering.inputs.epsilon = epsilon
    wf.connect(hemi_infosource, 'hemi', clustering, 'hemi')
    wf.connect(cluster_infosource, 'cluster', clustering, 'cluster_type')
    wf.connect(n_clusters_infosource, 'n_clusters', clustering, 'n_clusters')
    wf.connect(concat, 'simmatrix', clustering, 'in_File')

##reinflate to surface indices##
    clustermap = pe.Node(ClusterMap(), name = 'clustermap')
    wf.connect(clustering, 'out_File', clustermap, 'clusteredfile')
    wf.connect(concat, 'maskindex', clustermap, 'indicesfile')    

##Datasink##
    ds = pe.Node(nio.DataSink(), name="datasink")
    ds.inputs.base_directory = clusterdir
    wf.connect(concat,'simmatrix', ds, 'similarity')
    wf.connect(concat,'maskindex', ds, 'maskindex')
    wf.connect(clustermap, 'clustermapfile', ds, 'clustered')
    wf.write_graph()
    return wf

if __name__ == '__main__':
    wf = get_wf()               
    #wf.run(plugin="CondorDAGMan", plugin_args={"template":"universe = vanilla\nnotification = Error\ngetenv = true\nrequest_memory=4000"})
    try:
        wf.run(plugin="MultiProc", plugin_args={"n_procs":8})
    except OSError as e:
        print e.errno
        print e.filename
        print e.strerror
        pdb.set_trace()
    #wf.run(plugin='Linear')
