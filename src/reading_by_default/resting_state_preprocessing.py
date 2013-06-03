import os

import matplotlib
matplotlib.use('Agg')

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nipype.interfaces.fsl as fsl

display = os.environ["DISPLAY"]
os.environ.pop("DISPLAY")
from bips.workflows.scripts.u0a14c5b5899911e1bca80023dfa375f2.base import create_rest_prep
os.environ["DISPLAY"] = display

from bips.utils.reportsink.io import ReportSink
from nipype.utils.filemanip import list_to_filename

from variables import subjects, workingdir, resultsdir, freesurferdir
import os

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
    plot_tsnr.inputs.image_width = 600
    
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
    wf.base_dir = os.path.join(workingdir,"rs_preprocessing")
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
    
    subject_id_infosource = pe.Node(util.IdentityInterface(fields=['subject_id']), name="subject_id_infosource")
    subject_id_infosource.iterables = ("subject_id", subjects)
    
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id'], outfields=['resting_nifti']), 
                          name="datagrabber",
                          overwrite=True)
    datagrabber.inputs.base_directory = '/scr/namibia1/baird/MPI_Project/Neuroimaging_Data'
    datagrabber.inputs.template = '%s/%s/%s'
    datagrabber.inputs.template_args['resting_nifti'] = [['subject_id', 'func', '*.nii.gz']]
    datagrabber.inputs.sort_filelist = True
    
    wf.connect(subject_id_infosource, "subject_id", datagrabber, "subject_id")
    
    def get_tr_and_sliceorder(dicom_files, convention="french"):
        import numpy as np
        import dcmstack, dicom
        from dcmstack.dcmmeta import NiftiWrapper
        nii_wrp = NiftiWrapper.from_filename(dicom_files)
        if convention == "french":
            sliceorder = np.argsort(np.argsort(nii_wrp.meta_ext.get_values('CsaImage.MosaicRefAcqTimes')[0])).tolist()
        elif convention == "SPM":
            sliceorder = np.argsort(nii_wrp.meta_ext.get_values('CsaImage.MosaicRefAcqTimes')[0]).tolist()
        tr = nii_wrp.meta_ext.get_values('RepetitionTime')
        return tr/1000.,sliceorder
    
    get_meta = pe.Node(util.Function(input_names=['dicom_files', 'convention'], output_names=['tr', 'sliceorder'], function=get_tr_and_sliceorder), name="get_meta")
    get_meta.inputs.convention = "SPM"
    
    wf.connect(datagrabber, "resting_nifti", get_meta, "dicom_files")
    
    preproc = create_rest_prep(name="bips_resting_preproc", fieldmap=False)
    zscore = preproc.get_node('z_score')
    preproc.remove_nodes([zscore])
    
    mod_realign = preproc.get_node("mod_realign")
    mod_realign.plugin_args = {"submit_specs":"request_memory=4000\n"}
    
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
    preproc.get_node('fwhm_input').iterables = ('fwhm', [5])
    preproc.get_node('take_mean_art').get_node('strict_artifact_detect').inputs.save_plot = True
#preproc.get_node('take_mean_art').get_node('strict_artifact_detect').overwrite=True
    preproc.inputs.inputspec.ad_normthresh = 1
    preproc.inputs.inputspec.ad_zthresh = 3
    preproc.inputs.inputspec.do_slicetime = True
    preproc.inputs.inputspec.compcor_select = [True, True]
    preproc.inputs.inputspec.filter_type = 'fsl'
    preproc.get_node('bandpass_filter').iterables = [('highpass_freq', [100]), ('lowpass_freq', [10])]
#     preproc.inputs.inputspec.highpass_freq = 0.01
#     preproc.inputs.inputspec.lowpass_freq = 0.1
    #[motion_params, composite_norm, compcorr_components, global_signal, art_outliers, motion derivatives]
    preproc.inputs.inputspec.reg_params = [True, True, True, False, True, False]
    preproc.inputs.inputspec.fssubject_dir = freesurferdir
    wf.connect(get_meta, "tr", preproc, "inputspec.tr")
    wf.connect(get_meta, "sliceorder", preproc, "inputspec.sliceorder")
    wf.connect(subject_id_infosource, "subject_id", preproc, 'inputspec.fssubject_id')
    wf.connect(datagrabber, "resting_nifti", preproc, "inputspec.func")
    
 #   report_wf = create_preproc_report_wf(resultsdir + "/reports")
 #   report_wf.inputs.inputspec.fssubjects_dir = preproc.inputs.inputspec.fssubject_dir
    
    def pick_full_brain_ribbon(l):
        import os
        for path in l:
            if os.path.split(path)[1] == "ribbon.mgz":
                return path
            
 #   wf.connect(preproc,"artifactdetect.plot_files", report_wf, "inputspec.art_detect_plot")
 #   wf.connect(preproc,"take_mean_art.weighted_mean.mean_image", report_wf, "inputspec.mean_epi")
 #   wf.connect(preproc,("getmask.register.out_reg_file", list_to_filename), report_wf, "inputspec.reg_file")
 #   wf.connect(preproc,("getmask.fssource.ribbon",pick_full_brain_ribbon), report_wf, "inputspec.ribbon")
 #   wf.connect(preproc,("CompCor.tsnr.tsnr_file", list_to_filename), report_wf, "inputspec.tsnr_file")
 #   wf.connect(subject_id_infosource, "subject_id", report_wf, "inputspec.subject_id")
    
    ds = pe.Node(nio.DataSink(), name="datasink", overwrite=True)
    ds.inputs.base_directory = os.path.join(resultsdir, "volumes_bad_sliceorder")
    wf.connect(preproc, 'bandpass_filter.out_file', ds, "preprocessed_resting")
    wf.connect(preproc, 'getmask.register.out_fsl_file', ds, "func2anat_transform")
    wf.connect(preproc, 'outputspec.mask', ds, "epi_mask")
    wf.write_graph()
               
    wf.run(plugin="MultiProc")
