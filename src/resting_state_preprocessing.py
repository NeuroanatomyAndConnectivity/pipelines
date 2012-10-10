import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nipype.interfaces.fsl as fsl

from bips.workflows.scripts.u0a14c5b5899911e1bca80023dfa375f2.base import create_rest_prep
import os
from bips.utils.reportsink.io import ReportSink
from nipype.utils.filemanip import list_to_filename

subjects = os.listdir("/scr/namibia1/baird/MPI_Project/Neuroimaging_Data/")

subjects = ['11065.70',
'07070.79',
'13061.30',
'18066.85',
'10576.44',
'11944.79',
'11111.28',
'13536.51',
'14102.d1',
'12522.80',
'06222.f4',
'13649.8d',
'13565.7c',
'14018.65',
'14388.48',
'14110.f4',
'15006.be',
'03796.a8',
'10080.62',
'10581.e8',
'06275.e0',
'15475.c7',
'09561.e0',
'10960.82',
'14390.d3',
'17421.31',
'15466.cb',
'14702.ea',
'15403.c5',
'14081.cb',
'15890.ea',
'13989.a7',
'02231.e3',
'16101.0d',
'16939.4f',
'12184.55',
'07296.ec',
'16758.c3',
'12961.f8',
'12315.9a',
'15070.25',
'15640.65',
'18015.4c',
'14446.fb',
'14075.bd',
'16090.c9',
'19417.87',
'18761.dc',
'18758.73',
'17845.a2',
'18579.10',
'13085.b0',
'18094.87',
'16056.3d',
'10363.85',
'12339.39',
'09169.c5',
'14074.a7',
'13261.8d',
'11109.5c',
'19091.a3',
'16105.7a',
'11960.6a',
'13630.5d',
'09440.22',
'10439.86',
'11059.75',
'07346.36']

#short_seq_subjects = ['17815.6e', '12988.0e', '19032.10', '17765.54',
#                      '17819.fa', '15189.fb', '11400.94']
#subjects = [subject for subject in subjects if subject not in short_seq_subjects]

def create_preproc_report_wf(report_dir, name="preproc_report"):
    wf = pe.Workflow(name=name)
    
    inputspec = pe.Node(util.IdentityInterface(fields=['art_detect_plot', 
                                                       'mean_epi', 
                                                       'reg_file', 
                                                       'ribbon', 
                                                       'fssubjects_dir', 
                                                       'tsnr_file',
                                                       'report_name',
                                                       'subject_id']),
                        name="inputspec")
    
    def plot_epi_to_t1_coregistration(epi_file, reg_file, ribbon, fssubjects_dir):
        import pylab as plt 
        from nipy.labs import viz
        import nibabel as nb
        import numpy as np
        import os
        import nipype.interfaces.freesurfer as fs
        anat = nb.load(ribbon).get_data()
        anat[anat > 1] = 1
        anat_affine = nb.load(ribbon).get_affine()
        func = nb.load(epi_file).get_data()
        func_affine = nb.load(epi_file).get_affine()
        fig = plt.figure(figsize=(8, 6), edgecolor='k', facecolor='k')
        slicer = viz.plot_anat(np.asarray(func), np.asarray(func_affine), black_bg=True,
                                cmap=plt.cm.spectral,
                                cut_coords=(-6,3,12),
                                figure=fig,
                                axes=[0, .50, 1, .33]
                                )
        slicer.contour_map(np.asarray(anat), np.asarray(anat_affine), levels=[.51], colors=['r',])
        slicer.title("Mean EPI with cortical surface contour overlay (before registration)", size=12,
                     color='w', alpha=0)
        
        res = fs.ApplyVolTransform(source_file = epi_file,
                                reg_file = reg_file,
                                fs_target = True,
                                subjects_dir = fssubjects_dir).run()
                          
        func = nb.load(res.outputs.transformed_file).get_data()
        func_affine = nb.load(res.outputs.transformed_file).get_affine()
        slicer = viz.plot_anat(np.asarray(func), np.asarray(func_affine), black_bg=True,
                                cmap=plt.cm.spectral,
                                cut_coords=(-6,3,12),
                                figure=fig,
                                axes=[0, 0, 1, .33]
                                )
        slicer.contour_map(np.asarray(anat), np.asarray(anat_affine), levels=[.51], colors=['r',])
        slicer.title("Mean EPI with cortical surface contour overlay (after registration)", size=12,
                     color='w', alpha=0)
        plt.savefig("reg_plot.png", facecolor=fig.get_facecolor(), edgecolor='none')
        return os.path.abspath("reg_plot.png")
    
    plot_reg = pe.Node(util.Function(function=plot_epi_to_t1_coregistration, 
                                     input_names=['epi_file', 'reg_file', 'ribbon', 'fssubjects_dir'], 
                                     output_names=['plot_file']), name="plot_reg")
    wf.connect(inputspec, "mean_epi", plot_reg, "epi_file")
    wf.connect(inputspec, "reg_file", plot_reg, "reg_file")
    wf.connect(inputspec, "ribbon", plot_reg, "ribbon")
    wf.connect(inputspec, "fssubjects_dir", plot_reg, "fssubjects_dir")
    
    plot_tsnr = pe.Node(fsl.Slicer(), name="plot_tsnr")
    plot_tsnr.inputs.all_axial = True
    plot_tsnr.inputs.image_width = 400
    
    wf.connect(inputspec, "tsnr_file", plot_tsnr, "in_file")
    
    write_report = pe.Node(ReportSink(orderfields=["motion parameters", "tSNR", "coregistration"]), name="write_report")
    write_report.inputs.base_directory = report_dir
    
    def prepend_title(s_id):
        return "Resting state fMRI preprocessing report for " + s_id
    wf.connect(inputspec, ("subject_id", prepend_title),write_report, "report_name")
    wf.connect(inputspec, "art_detect_plot", write_report, "motion parameters")
    wf.connect(plot_tsnr, "out_file", write_report, "tSNR")
    wf.connect(plot_reg, "plot_file", write_report, "coregistration")
    
    return wf
    
if __name__ == '__main__':
    #subjects = ["14102.d1"]
    
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = "/Users/filo/workdir/rs_preprocessing/"
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
    
    subject_id_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_id_infosource")
    subject_id_infosource.iterables = ("subject_id", subjects)
    
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=['resting_dicoms','resting_nifti','t1_nifti']), name="datagrabber")
    datagrabber.inputs.base_directory = '/scr/namibia1/baird/MPI_Project/Neuroimaging_Data/'
    datagrabber.inputs.template = '%s/%s/%s'
    datagrabber.inputs.template_args['resting_dicoms'] = [['subject_id', '*resting*', '*']]
    datagrabber.inputs.template_args['resting_nifti'] = [['subject_id', 'func', '*.nii.gz']]
    datagrabber.inputs.template_args['t1_nifti'] = [['subject_id', 'anat', '*.nii.gz']]
    datagrabber.inputs.sort_filelist = True
    
    wf.connect(subject_id_infosource, "subject_id", datagrabber, "subject_id")
    
    def get_tr_and_sliceorder(dicom_files):
        import numpy as np
        import dcmstack, dicom
        my_stack = dcmstack.DicomStack()
        for src_path in dicom_files:
            src_dcm = dicom.read_file(src_path)
            my_stack.add_dcm(src_dcm)
        nii_wrp = my_stack.to_nifti_wrapper()
        sliceorder = np.argsort(nii_wrp.meta_ext.get_values('CsaImage.MosaicRefAcqTimes')[0]).tolist()
        tr = nii_wrp.meta_ext.get_values('RepetitionTime')
        return tr/1000.,sliceorder
    
    get_meta = pe.Node(util.Function(input_names=['dicom_files'], output_names=['tr', 'sliceorder'], function=get_tr_and_sliceorder), name="get_meta")
    
    wf.connect(datagrabber, "resting_dicoms", get_meta, "dicom_files")
    
    preproc = create_rest_prep(name="bips_resting_preproc", fieldmap=False)
    zscore = preproc.get_node('z_score')
    preproc.remove_nodes([zscore])
    
    #workaround for realignment crashing in multiproc environment
    #mod_realign = preproc.get_node("mod_realign")
    #mod_realign.run_without_submitting = True
    
    # inputs
    preproc.inputs.inputspec.motion_correct_node = 'nipy'
    preproc.inputs.inputspec.realign_parameters = {"loops":[5],
                                                   "speedup":[5]}
    preproc.inputs.inputspec.do_whitening = False
    preproc.inputs.inputspec.timepoints_to_remove = 4
    preproc.inputs.inputspec.smooth_type = 'susan'
    preproc.inputs.inputspec.do_despike = False
    preproc.inputs.inputspec.surface_fwhm = 0.0
    preproc.inputs.inputspec.num_noise_components = 6
    preproc.inputs.inputspec.regress_before_PCA = False
    preproc.get_node('fwhm_input').iterables = ('fwhm', [0,5])
    preproc.get_node('take_mean_art').get_node('strict_artifact_detect').inputs.save_plot = True
    preproc.inputs.inputspec.ad_normthresh = 1
    preproc.inputs.inputspec.ad_zthresh = 3
    preproc.inputs.inputspec.do_slicetime = True
    preproc.inputs.inputspec.compcor_select = [True, True]
    preproc.inputs.inputspec.filter_type = 'fsl'
    preproc.inputs.inputspec.highpass_freq = 100
    preproc.inputs.inputspec.lowpass_freq = 10
    preproc.inputs.inputspec.reg_params = [True, True, True, False, True, False]
    preproc.inputs.inputspec.fssubject_dir = '/scr/namibia1/baird/MPI_Project/freesurfer/'
    
    wf.connect(get_meta, "tr", preproc, "inputspec.tr")
    wf.connect(get_meta, "sliceorder", preproc, "inputspec.sliceorder")
    wf.connect(subject_id_infosource, "subject_id", preproc, 'inputspec.fssubject_id')
    wf.connect(datagrabber, "resting_nifti", preproc, "inputspec.func")
    
    results_dir = '/Users/filo/results'
    report_wf = create_preproc_report_wf(results_dir + "/reports")
    report_wf.inputs.inputspec.fssubjects_dir = preproc.inputs.inputspec.fssubject_dir
    
    def pick_full_brain_ribbon(l):
        import os
        for path in l:
            if os.path.split(path)[1] == "ribbon.mgz":
                return path
            
    wf.connect(preproc,"artifactdetect.plot_files", report_wf, "inputspec.art_detect_plot")
    wf.connect(preproc,"take_mean_art.weighted_mean.mean_image", report_wf, "inputspec.mean_epi")
    wf.connect(preproc,("getmask.register.out_reg_file", list_to_filename), report_wf, "inputspec.reg_file")
    wf.connect(preproc,("getmask.fssource.ribbon",pick_full_brain_ribbon), report_wf, "inputspec.ribbon")
    wf.connect(preproc,("CompCor.tsnr.tsnr_file", list_to_filename), report_wf, "inputspec.tsnr_file")
    wf.connect(subject_id_infosource, "subject_id", report_wf, "inputspec.subject_id")
    
    ds = pe.Node(nio.DataSink(), name="datasink")
    ds.inputs.base_directory = results_dir + "/volumes"
    wf.connect(preproc, 'bandpass_filter.out_file', ds, "preprocessed_resting")
    wf.connect(preproc, 'getmask.register.out_fsl_file', ds, "func2anat_transform")
    wf.connect(preproc, 'outputspec.mask', ds, "epi_mask")
    wf.write_graph()
               
    wf.run(plugin="IPython", plugin_args={'n_procs':4})