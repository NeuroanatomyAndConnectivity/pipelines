import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import os
#from nipype.interfaces.dcmstack import DcmStack
from nipype.interfaces.freesurfer.preprocess import ReconAll

#bring in subject and study specific data and dirs
from variables import working_dir, freesurfer_dir, subjects_M, subjects_NM

nii_base_dir = "/scr/alaska1/steele/BSL_IHI/T1w/"

if __name__ == '__main__':
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(working_dir,"preprecossing")
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
    
    subjects_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_infosource")
    subjects = ['M/' + subject for subject in subjects_M] + ['NM/' + subject for subject in subjects_NM]
    subjects_infosource.iterables = ('subject_id', subjects)
    
    #this one is for bob
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=['t1w']), 
                          name="datagrabber")
    datagrabber.inputs.base_directory = nii_base_dir
    datagrabber.inputs.template = '%s/%s'
    datagrabber.inputs.template_args['t1w'] = [['subject_id', '*.nii']]
    datagrabber.inputs.sort_filelist = True

    wf.connect(subjects_infosource, "subject_id", datagrabber, "subject_id")
    
    recon_all = pe.Node(ReconAll(), name="recon_all")
    recon_all.plugin_args={'submit_specs': 'request_memory = 2500'}
    #recon_all.inputs.subjects_dir = "/scr/adenauer1/freesurfer"
	
	 # link datagrabber stuff to workflow
    wf.connect(datagrabber, "t1w", recon_all, "T1_files")
    
    # replace / in subject id string with a _
    def sub_id(id):
        return id.replace('/','_')
    #connect also works with functions, this runs sub_id (magic)
    wf.connect(subjects_infosource, ("subject_id", sub_id) , recon_all, "subject_id") #setup to run reconall on datagrabber input

    def cat(s1, s2):
        import os
        return os.path.join(s1, s2)
    join = pe.Node(util.Function(input_names=['s1', 's2'], output_names=['out'], function=cat), name="join")
    wf.connect(recon_all, 'subjects_dir', join, 's1')
    wf.connect(recon_all, 'subject_id', join, 's2')
    
    ds2 = pe.Node(nio.DataSink(), name="datasink") # put datasink interface inside this node
    ds2.inputs.base_directory = freesurfer_dir # this is the base dir for output from freesurfer
    ds2.inputs.regexp_substitutions = [('_subject_id_*/', '')] # this changes filepaths so that freesurfer is happy :)
    wf.connect(join, "out", ds2, "freesurfer")
    
    wf.run(plugin="CondorDAGMan")
                          
                          
    
