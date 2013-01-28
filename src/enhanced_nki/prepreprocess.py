import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import os
from nipype.interfaces.dcmstack import DcmStack
from nipype.interfaces.freesurfer.preprocess import ReconAll




subjects = [
 '0185676',
 '0179309',
 '0103645',
 '0116039',
 '0198357',
 '0132717',
 '0195031',
 '0182376',
 '0153790',
 '0118439',
 '0136018',
 '0144667',
 '0151580',
 '0186277',
 '0115321',
 '0133894',
 '0160099',
 '0164326',
 '0173496',
 '0117168',
 '0192197',
 '0122816',
 '0122169',
 '0166009',
 '0181439',
 '0179283',
 '0155419',
 '0188199',
 '0194956',
 '0197570',
 '0168489',
 '0166987',
 '0190501',
 '0105290',
 '0150525',
 '0152968',
 '0179873',
 '0199155',
 '0177681',
 '0154419',
 '0179454',
 '0193358',
 '0156263',
 '0155458',
 '0137073',
 '0116834',
 '0109727',
 '0178174',
 '0198130',
 '0185428',
 '0131832',
 '0199340',
 '0132995',
 '0105521',
 '0146865',
 '0182604',
 '0183457',
 '0198051',
 '0126919',
 '0159429',
 '0137714',
 '0125762',
 '0168013',
 '0178453',
 '0164900',
 '0130249',
 '0190053',
 '0112347',
 '0147122',
 '0112828',
 '0137496',
 '0136416',
 '0112249',
 '0123657',
 '0109459',
 '0195236',
 '0120557',
 '0118051',
 '0105488',
 '0158411',
 '0161200',
 '0136303',
 '0106780',
 '0127733',
 '0141795',
 '0121498',
 '0138558',
 '0174363',
 '0139212',
 '0144314',
 '0137679',
 '0196651',
 '0150589',
 '0197456',
 '0173286',
 '0127800',
 '0161513',
 '0144344',
 '0188939',
 '0148071',
 '0122512',
 '0179005',
 '0122844',
 '0192736',
 '0198985',
 '0106057',
 '0134795',
 '0115824',
 '0120652',
 '0188219',
 '0108355',
 '0156678',
 '0180308',
 '0162902',
 '0168413',
 '0153114',
 '0177330',
 '0152189',
 '0113013',
 '0163059',
 '0132088',
 '0144702',
 '0146714',
 '0154423',
 '0170363',
 '0187635',
 '0167827',
 '0135671',
 '0116415',
 '0131127',
 '0102157',
 '0111282',
 '0177857',
 '0186697',
 '0132850',
 '0183726',
 '0149794',
 '0171266',
 '0165532',
 '0115454',
 '0116065',
 '0115564',
 '0123429',
 '0165660',
 '0162251',
 '0157947',
 '0162704',
 '0199620',
 '0123971',
 '0114232',
 '0119866',
 '0194023',
 '0150716',
 '0103714',
 '0103872',
 '0139480',
 '0168357',
 '0197836',
 '0152384',
 '0196558',
 '0158744',
 '0139300',
 '0185781',
 '0116842',
 '0157873',
 '0189478',
 '0109819',
 '0113030',
 '0174886',
 '0180093',
 '0168239',
 '0188854',
 '0153131',
 '0169007',
 '0120538',
 '0173085',
 '0144495',
 '0141473',
 '0123173',
 '0158560',
 '0133436']

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
                          name="datagrabber",
                          overwrite=True)
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
    recon_all.plugin_args={'submit_specs': 'request_memory = 3000'}
    #recon_all.inputs.subjects_dir = "/scr/adenauer1/freesurfer"
    wf.connect(dcm2nii_t1, "out_file", recon_all, "T1_files")
    wf.connect(subjects_infosource, "subject_id", recon_all, "subject_id")
    
    
    wf.run(plugin="CondorDAGMan")
                          
                          
    