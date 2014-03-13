import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import os
from nipype.interfaces.dcmstack import DcmStack
from nipype.interfaces.freesurfer.preprocess import ReconAll

from variables import subjects
brain_database_dir = '/afs/cbs/probands/bdb/'
workingdir = "/scr/adenauer1/workingdir"

def getdata(basedir, subject_id):
    subject_dict = {'03088.88': '/afs/cbs/probands/bdb/03088.88/03088.88_130218_072939_S3_t2star_epi_2D_standard_rest.tar.gz',
 '03196.94': '/afs/cbs/probands/bdb/03196.94/03196.94_130429_111637_S4_t2star_epi_2D_standard_rest.tar.gz',
 '03796.a8': '/afs/cbs/probands/bdb/03796.a8/03796.a8_120206_S11_t2star_epi_2D_resting.tar.gz',
 '06222.f4': '/afs/cbs/probands/bdb/06222.f4/06222.f4_120507_S7_t2star_epi_2D_resting.tar.gz',
 '07135.97': '/afs/cbs/probands/bdb/07135.97/07135.97_120130_S5_t2star_epi_2D_resting.tar.gz',
 '07296.ec': '/afs/cbs/probands/bdb/07296.ec/07296.ec_130219_082245_S3_t2star_epi_2D_standard_rest.tar.gz',
 '08940.88': '/afs/cbs/probands/bdb/08940.88/08940.88_130212_091915_S3_t2star_epi_2D_standard_rest.tar.gz',
 '08950.3f': '/afs/cbs/probands/bdb/08950.3f/08950.3f_130122_105738_S3_t2star_epi_2D_standard_rest.tar.gz',
 '09440.22': '/afs/cbs/probands/bdb/09440.22/09440.22_120216_S5_t2star_epi_2D_resting.tar.gz',
 '10080.62': '/afs/cbs/probands/bdb/10080.62/10080.62_120214_S5_t2star_epi_2D_resting.tar.gz',
 '10149.5b': '/afs/cbs/probands/bdb/10149.5b/10149.5b_120213_S12_t2star_epi_2D_resting.tar.gz',
 '10282.53': '/afs/cbs/probands/bdb/10282.53/10282.53_130205_083239_S3_t2star_epi_2D_standard_rest.tar.gz',
 '10340.b4': '/afs/cbs/probands/bdb/10340.b4/10340.b4_130429_122030_S3_t2star_epi_2D_standard_rest.tar.gz',
 '11981.75': '/afs/cbs/probands/bdb/11981.75/11981.75_130313_141454_S3_t2star_epi_2D_standard_rest.tar.gz',
 '12184.55': '/afs/cbs/probands/bdb/12184.55/12184.55_120222_S5_t2star_epi_2D_resting.tar.gz',
 '12522.80': '/afs/cbs/probands/bdb/12522.80/12522.80_120222_S12_t2star_epi_2D_resting.tar.gz',
 '12855.d4': '/afs/cbs/probands/bdb/12855.d4/12855.d4_130219_105255_S3_t2star_epi_2D_standard_rest.tar.gz',
 '12961.f8': '/afs/cbs/probands/bdb/12961.f8/12961.f8_120502_S7_t2star_epi_2D_resting.tar.gz',
 '13061.30': '/afs/cbs/probands/bdb/13061.30/13061.30_120216_S5_t2star_epi_2D_resting.tar.gz',
 '13338.a9': '/afs/cbs/probands/bdb/13338.a9/13338.a9_130218_115951_S3_t2star_epi_2D_standard_rest.tar.gz',
 '13565.7c': '/afs/cbs/probands/bdb/13565.7c/13565.7c_120213_S5_t2star_epi_2D_resting.tar.gz',
 '13713.95': '/afs/cbs/probands/bdb/13713.95/13713.95_120206_S11_t2star_epi_2D_resting.tar.gz',
 '13742.1d': '/afs/cbs/probands/bdb/13742.1d/13742.1d_130122_080858_S3_t2star_epi_2D_standard_rest.tar.gz',
 '13952.73': '/afs/cbs/probands/bdb/13952.73/13952.73_120130_S5_t2star_epi_2D_resting.tar.gz',
 '13953.3c': '/afs/cbs/probands/bdb/13953.3c/13953.3c_130312_085135_S3_t2star_epi_2D_standard_rest.tar.gz',
 '14018.65': '/afs/cbs/probands/bdb/14018.65/14018.65_120222_S5_t2star_epi_2D_resting.tar.gz',
 '14075.bd': '/afs/cbs/probands/bdb/14075.bd/14075.bd_120130_S5_t2star_epi_2D_resting.tar.gz',
 '14102.d1': '/afs/cbs/probands/bdb/14102.d1/14102.d1_130212_082756_S3_t2star_epi_2D_standard_rest.tar.gz',
 '14151.97': '/afs/cbs/probands/bdb/14151.97/14151.97_120507_S7_t2star_epi_2D_resting.tar.gz',
 '14390.d3': '/afs/cbs/probands/bdb/14390.d3/14390.d3_120214_S5_t2star_epi_2D_resting.tar.gz',
 '14702.ea': '/afs/cbs/probands/bdb/14702.ea/14702.ea_120305_S7_t2star_epi_2D_resting.tar.gz',
 '14748.0a': '/afs/cbs/probands/bdb/14748.0a/14748.0a_130122_084018_S3_t2star_epi_2D_standard_rest.tar.gz',
 '14839.09': '/afs/cbs/probands/bdb/14839.09/14839.09_130218_153205_S3_t2star_epi_2D_standard_rest.tar.gz',
 '14945.a7': '/afs/cbs/probands/bdb/14945.a7/14945.a7_120206_S10_t2star_epi_2D_resting.tar.gz',
 '15070.25': '/afs/cbs/probands/bdb/15070.25/15070.25_130617_100946_S3_t2star_epi_2D_standard_rest.tar.gz',
 '15155.03': '/afs/cbs/probands/bdb/15155.03/15155.03_130319_084527_S3_t2star_epi_2D_standard_rest.tar.gz',
 '15189.fb': '/afs/cbs/probands/bdb/15189.fb/15189.fb_130305_084751_S3_t2star_epi_2D_standard_rest.tar.gz',
 '15443.fd': '/afs/cbs/probands/bdb/15443.fd/15443.fd_120305_S7_t2star_epi_2D_resting.tar.gz',
 '15466.cb': '/afs/cbs/probands/bdb/15466.cb/15466.cb_120305_S7_t2star_epi_2D_resting.tar.gz',
 '15826.16': '/afs/cbs/probands/bdb/15826.16/15826.16_130516_112134_S3_t2star_epi_2D_standard_rest.tar.gz',
 '15890.ea': '/afs/cbs/probands/bdb/15890.ea/15890.ea_120214_S5_t2star_epi_2D_resting.tar.gz',
 '16049.a3': '/afs/cbs/probands/bdb/16049.a3/16049.a3_120308_S9_t2star_epi_2D_resting.tar.gz',
 '16056.3d': '/afs/cbs/probands/bdb/16056.3d/16056.3d_120521_S7_t2star_epi_2D_resting.tar.gz',
 '16090.c9': '/afs/cbs/probands/bdb/16090.c9/16090.c9_120305_S7_t2star_epi_2D_resting.tar.gz',
 '16341.95': '/afs/cbs/probands/bdb/16341.95/16341.95_130207_105210_S3_t2star_epi_2D_standard_rest.tar.gz',
 '17421.31': '/afs/cbs/probands/bdb/17421.31/17421.31_130226_104750_S3_t2star_epi_2D_standard_rest.tar.gz',
 '17711.9f': '/afs/cbs/probands/bdb/17711.9f/17711.9f_130129_071718_S3_t2star_epi_2D_standard_rest.tar.gz',
 '18256.89': '/afs/cbs/probands/bdb/18256.89/18256.89_130319_114128_S3_t2star_epi_2D_standard_rest.tar.gz',
 '18928.9c': '/afs/cbs/probands/bdb/18928.9c/18928.9c_130508_093906_S12_t2star_epi_2D_standard_rest.tar.gz',
 '19443.00': '/afs/cbs/probands/bdb/19443.00/19443.00_130305_080524_S3_t2star_epi_2D_standard_rest.tar.gz',
 '19717.75': '/afs/cbs/probands/bdb/19717.75/19717.75_130218_083322_S3_t2star_epi_2D_standard_rest.tar.gz',
 '19883.56': '/afs/cbs/probands/bdb/19883.56/19883.56_130218_141716_S3_t2star_epi_2D_standard_rest.tar.gz',
 '21306.b6': '/afs/cbs/probands/bdb/21306.b6/21306.b6_130313_153159_S3_t2star_epi_2D_standard_rest.tar.gz',
 '21359.41': '/afs/cbs/probands/bdb/21359.41/21359.41_130516_073454_S3_t2star_epi_2D_standard_rest.tar.gz'}
    import os
    t1_keywords = ['t1_mpr_sag_ADNI_32Ch',
                   't1_mpr_sag_standard',
                   't1_MPRAGE_MPIL_32Ch',
                   't1_mpr_sag_ADNI_12Ch',
                   't1_mpr_sag_standard_32Ch_wasserexc',
                   't1_mpr_sag_standard_12Ch',
                   't1_mpr_sag_kids_12Ch',
                   't1_mprage_ADNI']
    t1s = []
    #print '\n'.join(os.listdir(os.path.join(basedir, subject_id)))
    files = os.listdir(os.path.join(basedir, subject_id))
    files.sort()
    for f in files:
        for k in t1_keywords:
            if k in f and f.endswith("tar.gz"):
                if k in t1_keywords:
                    t1s.append(os.path.join(basedir, subject_id, f))
                continue
    resting = subject_dict[subject_id]
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


