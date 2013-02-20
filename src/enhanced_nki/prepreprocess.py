import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import os
from nipype.interfaces.dcmstack import DcmStack
from nipype.interfaces.freesurfer.preprocess import ReconAll



#subjects = [subjects[0]]

nki_dicom_dir = "/scr/kalifornien1/data/nki_enhanced/dicoms"
#brain_database_dir = '/scr/adenauer1/dicoms/'
workingdir = "/scr/kansas1/workingdir/nki"

if __name__ == '__main__':
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(workingdir,"preprecossing")
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
    
    subjects_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_infosource")
    subjects_infosource.iterables = ('subject_id', subjects)
    
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=['t1', 'others']), 
                          name="datagrabber")
    datagrabber.inputs.base_directory = nki_dicom_dir
    datagrabber.inputs.template = '%s/%s/'
    datagrabber.inputs.template_args['t1'] = [['subject_id', 'anat']]
    datagrabber.inputs.template_args['others'] = [['subject_id', ['session_1/DTI_mx_137', 'session_1/RfMRI_mx_1400', 'session_1/RfMRI_mx_645', 'session_1/RfMRI_std_2500']]]
    datagrabber.inputs.sort_filelist = True

    wf.connect(subjects_infosource, "subject_id", datagrabber, "subject_id")

    dcm2nii_t1 = pe.Node(DcmStack(), name="dcm2nii_t1")
    dcm2nii_t1.inputs.embed_meta = True
    dcm2nii_t1.plugin_args={'submit_specs': 'request_memory = 2000'}
    wf.connect(datagrabber, "t1",  dcm2nii_t1, "dicom_files")
    
    dcm2nii_others = pe.MapNode(DcmStack(), name="dcm2nii_others", iterfield=['dicom_files'])
    dcm2nii_others.inputs.embed_meta = True
    dcm2nii_others.plugin_args={'submit_specs': 'request_memory = 2000'}
    wf.connect(datagrabber, "others", dcm2nii_others, "dicom_files")
    
    recon_all = pe.Node(ReconAll(), name="recon_all")
    recon_all.plugin_args={'submit_specs': 'request_memory = 2500'}
    #recon_all.inputs.subjects_dir = "/scr/adenauer1/freesurfer"
    wf.connect(dcm2nii_t1, "out_file", recon_all, "T1_files")
    wf.connect(subjects_infosource, "subject_id", recon_all, "subject_id")
    
    t1_rename = pe.Node(util.Rename(format_string="anat.nii.gz"), name="t1_rename")
    wf.connect(dcm2nii_t1, "out_file", t1_rename, "in_file")
    
    others_rename = pe.MapNode(util.Rename(), name="others_rename", iterfield= ['format_string', 'in_file'])
    others_rename.inputs.format_string = ['DTI_mx_137.nii.gz', 'RfMRI_mx_1400.nii.gz', 'RfMRI_mx_645.nii.gz', 'RfMRI_std_2500.nii.gz']
    wf.connect(dcm2nii_others, "out_file", others_rename, "in_file")
    
    ds = pe.Node(nio.DataSink(), name="datasink")
    ds.inputs.base_directory = '/scr/kalifornien1/data/nki_enhanced/'
    ds.inputs.substitutions = [('_subject_id_', '')]
    ds.inputs.regexp_substitutions = [('_others_rename[0-9]*/', '')]
    wf.connect(t1_rename, "out_file", ds, "niftis.@t1")
    wf.connect(others_rename, "out_file", ds, "niftis.@others")
    
    def cat(s1, s2):
        import os
        return os.path.join(s1, s2)
    join = pe.Node(util.Function(input_names=['s1', 's2'], output_names=['out'], function=cat), name="join")
    wf.connect(recon_all, 'subjects_dir', join, 's1')
    wf.connect(recon_all, 'subject_id', join, 's2')
    
    ds2 = pe.Node(nio.DataSink(), name="datasink2")
    ds2.inputs.base_directory = '/scr/kalifornien1/data/nki_enhanced/'
    ds2.inputs.regexp_substitutions = [('_subject_id_[0-9]*/', '')]
    wf.connect(join, "out", ds2, "freesurfer")
    
    wf.run(plugin="CondorDAGMan")
                          
                          
    