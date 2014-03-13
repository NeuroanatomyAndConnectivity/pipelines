import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import os
from nipype.interfaces.dcmstack import DcmStack
from nipype.interfaces.freesurfer.preprocess import ReconAll
from nipype.interfaces.dcm2nii import Dcm2nii



#subjects = [subjects[0]]

subjects = ['0101084',
 '0106664',
 '0108184',
 '0108781',
 '0110809',
 '0112536',
 '0114008',
 '0115684',
 '0117902',
 '0117964',
 '0119351',
 '0120818',
 '0120859',
 '0121400',
 '0123048',
 '0123116',
 '0124714',
 '0125107',
 '0126369',
 '0127665',
 '0127784',
 '0130424',
 '0130678',
 '0132049',
 '0133646',
 '0134505',
 '0135591',
 '0138497',
 '0139437',
 '0141860',
 '0142609',
 '0143484',
 '0150062',
 '0158726',
 '0160872',
 '0166731',
 '0167693',
 '0168007',
 '0169571',
 '0170636',
 '0172228',
 '0176479',
 '0178964',
 '0184446',
 '0187884',
 '0196198',
 '0123657', 
 '0164385',
 '0171391']


nki_dicom_dir = "/scr/kalifornien1/data/nki_enhanced/dicoms"
#brain_database_dir = '/scr/adenauer1/dicoms/'
workingdir = "/scr/kansas1/workingdir/nki"

if __name__ == '__main__':
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(workingdir,"preprecossing")
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
    
    subjects_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_infosource")
    subjects_infosource.iterables = ('subject_id', subjects)
    
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=['t1', 'dwi', 'others']), 
                          name="datagrabber")
    datagrabber.inputs.base_directory = nki_dicom_dir
    datagrabber.inputs.template = '%s/%s'
    datagrabber.inputs.template_args['t1'] = [['subject_id', 'anat']]
    datagrabber.inputs.template_args['others'] = [['subject_id', ['session_1/RfMRI_mx_645', 'session_1/RfMRI_std_2500']]]
    datagrabber.inputs.template_args['dwi'] = [['subject_id', ['session_1/DTI_mx_137/*']]]
    datagrabber.inputs.sort_filelist = True

    wf.connect(subjects_infosource, "subject_id", datagrabber, "subject_id")

    dcm2nii_t1 = pe.Node(DcmStack(), name="dcm2nii_t1")
    dcm2nii_t1.inputs.embed_meta = True
    dcm2nii_t1.plugin_args={'submit_specs': 'request_memory = 2000'}
    wf.connect(datagrabber, "t1",  dcm2nii_t1, "dicom_files")
    
    dcm2nii_dwi = pe.Node(Dcm2nii(), name="dcm2nii_dwi")
    dcm2nii_dwi.inputs.gzip_output = True
    dcm2nii_dwi.inputs.nii_output = True
    dcm2nii_dwi.inputs.anonymize = False
    dcm2nii_dwi.plugin_args={'submit_specs': 'request_memory = 2000'}
    wf.connect(datagrabber, "dwi",  dcm2nii_dwi, "source_names")
    
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
    
    dwi_rename = pe.Node(util.Rename(format_string="DTI_mx_137.nii.gz"), name="dwi_rename")
    wf.connect(dcm2nii_dwi, "converted_files", dwi_rename, "in_file")
    
    bvecs_rename = pe.Node(util.Rename(format_string="DTI_mx_137.bvecs"), name="bvecs_rename")
    wf.connect(dcm2nii_dwi, "bvecs", bvecs_rename, "in_file")
    
    bvals_rename = pe.Node(util.Rename(format_string="DTI_mx_137.bvals"), name="bvals_rename")
    wf.connect(dcm2nii_dwi, "bvals", bvals_rename, "in_file")
    
    others_rename = pe.MapNode(util.Rename(), name="others_rename", iterfield= ['format_string', 'in_file'])
    others_rename.inputs.format_string = ['RfMRI_mx_645.nii.gz', 'RfMRI_std_2500.nii.gz']
    wf.connect(dcm2nii_others, "out_file", others_rename, "in_file")
    
    ds = pe.Node(nio.DataSink(), name="datasink")
    ds.inputs.base_directory = '/scr/kalifornien1/data/nki_enhanced/'
    ds.inputs.substitutions = [('_subject_id_', '')]
    ds.inputs.regexp_substitutions = [('_others_rename[0-9]*/', '')]
    wf.connect(t1_rename, "out_file", ds, "niftis.@t1")
    wf.connect(dwi_rename, "out_file", ds, "niftis.@dwi")
    wf.connect(bvals_rename, "out_file", ds, "niftis.@bvecs")
    wf.connect(bvecs_rename, "out_file", ds, "niftis.@bvals")
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
    
    wf.run(plugin="CondorDAGMan", plugin_args={'submit_specs': 'request_memory = 2500 \n notify_user = gorgolewski@cbs.mpg.de, aschaefer@cbs.mpg.de'})
                          
                          
    