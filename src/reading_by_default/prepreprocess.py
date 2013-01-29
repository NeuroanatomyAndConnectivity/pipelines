import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import os
from nipype.interfaces.dcmstack import DcmStack
from nipype.interfaces.freesurfer.preprocess import ReconAll




subjects = [
#'13649.8d',
'11065.70',
##'13224.69', #missing from the bdb
#'19079.ca',
#'18015.4c',
#'10145.c2',
#'18693.4a',
#'18066.85',
#'12827.36',
#'13061.30'
]
brain_database_dir = '/scr/adenauer1/dicoms/'
workingdir = "/scr/adenauer1/workingdir"

def getdata(basedir, subject_id):
    import os
    t1_keywords = ['t1_mpr_sag_ADNI_32Ch', 
                   't1_mpr_sag_standard', 
                   't1_MPRAGE_MPIL_32Ch', 
                   't1_mpr_sag_ADNI_12Ch', 
                   't1_mpr_sag_standard_32Ch_wasserexc',
                   't1_mpr_sag_standard_12Ch',
                   't1_mpr_sag_kids_12Ch',
                   't1_mprage_ADNI']
    resting_keywords = ['t2star_epi_2D_resting', 
                        'ep2dap_resting', 
                        'ep2d_resting_SartMW', 
                        'ep2d_bold_resting',
                        'ep2dapREST',
                        't2star_epi_2D_standard_REST2',
                        't2star_epi_2D_standard_REST1',
                        't2star_epi_resting_12Ch',
                        't2star_epi_2D_3x3x3_resting']
    restings = []
    t1s = []
    #print '\n'.join(os.listdir(os.path.join(basedir, subject_id)))
    files = os.listdir(os.path.join(basedir, subject_id))
    files.sort()
    for f in files:
        for k in t1_keywords + resting_keywords:
            if k in f and f.endswith("tar.gz"):
                if k in t1_keywords:
                    t1s.append(os.path.join(basedir, subject_id, f))
                else:
                    restings.append(os.path.join(basedir, subject_id, f))
                continue
    print "More than one resting state!"
    resting = restings[-3]
    return(t1s[-1], resting)

for subject_id in subjects:
    print getdata(brain_database_dir, subject_id)

if __name__ == '__main__':
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(workingdir,"preprecossing")
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
    
    subjects_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_infosource")
    subjects_infosource.iterables = ('subject_id', subjects)
    
    datagrabber = pe.Node(util.Function(input_names=['basedir', 'subject_id'], 
                                        output_names=['t1s', 'resting'], 
                                        function=getdata), name = "datagrabber")
    datagrabber.inputs.basedir = brain_database_dir
    wf.connect(subjects_infosource, "subject_id", datagrabber, "subject_id")
    
    def gunzip(file):
        import os
        os.mkdir("./out")
        from nipype.interfaces.base import CommandLine
        c = CommandLine(command="tar zxvf %s"%file)
        c.run()
        from nipype.utils.filemanip import split_filename
        _,base,_  = split_filename(file)
        
        return os.path.abspath(base)
    
    t1s_gunzip = pe.Node(util.Function(input_names=['file'], 
                                        output_names=['dir'], 
                                        function=gunzip), name = "t1s_gunzip")
    wf.connect(datagrabber, "t1s", t1s_gunzip, "file")
    resting_gunzip = pe.Node(util.Function(input_names=['file'], 
                                        output_names=['dir'], 
                                        function=gunzip), name = "resting_gunzip")
    wf.connect(datagrabber, "resting", resting_gunzip, "file")
    
#    dcm2nii_t1s = pe.Node(DcmStack(), name="dcm2nii_t1s")
#    dcm2nii_t1s.inputs.embed_meta = True
#    wf.connect(t1s_gunzip, "dir", dcm2nii_t1s, "dicom_files")
    
    dcm2nii_resting = pe.Node(DcmStack(), name="dcm2nii_resting")
    dcm2nii_resting.inputs.embed_meta = True
    def add_asterix(s):
        return s + "/*"
    wf.connect(resting_gunzip, ("dir",add_asterix), dcm2nii_resting, "dicom_files")
    
#    recon_all = pe.Node(ReconAll(), name="recon_all")
#    #recon_all.inputs.subjects_dir = "/scr/adenauer1/freesurfer"
#    wf.connect(dcm2nii_t1s, "out_file", recon_all, "T1_files")
#    wf.connect(subjects_infosource, "subject_id", recon_all, "subject_id")
    
    wf.run(plugin="Linear")
                          
                          
    