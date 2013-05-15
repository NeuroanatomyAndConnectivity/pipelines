import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nipype.interfaces.ants as ants
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
from nipype.workflows.smri.ants.antsRegistrationBuildTemplate import antsRegistrationTemplateBuildSingleIterationWF
import os
from variables import workingdir, freesurferdir, subjects, resultsdir
from nipype.interfaces.ants.registration import Registration
from nipype.interfaces.ants.resampling import ApplyTransforms
import nipype.interfaces.c3 as c3


def create_custom_template(name="create_custom_template", n_iterations = 6):
    tbuilder = pe.Workflow(name=name)
    inputspec = pe.Node(util.IdentityInterface(fields=["t1_volumes"]), name="inputspec")
    
    N4biasfield = pe.MapNode(ants.N4BiasFieldCorrection(), name="N4biasfield", iterfield=['input_image'])
    N4biasfield.inputs.bspline_fitting_distance = 300
    N4biasfield.inputs.shrink_factor = 3
    N4biasfield.inputs.n_iterations = [50,50,30,20]
    N4biasfield.inputs.convergence_threshold = 1e-6
    N4biasfield.inputs.num_threads = 1
    
    tbuilder.connect(inputspec, "t1_volumes", N4biasfield, "input_image")
#    tbuilder.connect(inputspec, "masks", N4biasfield, "mask_image")
    import nipype.interfaces.c3 as c3
#     initAvg = pe.Node(interface=ants.AverageImages(), name ='initAvg')
#     initAvg.inputs.dimension = 3
#     initAvg.inputs.normalize = True
# 
#     tbuilder.connect(N4biasfield, "output_image", initAvg, "images")
#     
# #    sumMask = pe.Node(interface=ants.AverageImages(), name ='sumMask')
# #    sumMask.inputs.dimension = 3
# #    sumMask.inputs.normalize = False
# 
# #    tbuilder.connect(inputspec, "masks", sumMask, "images")
#     
#     prev_step_output = (initAvg, 'output_average_image')
#     
    def make_dict(l):
        out = []
        for i in l:
            out.append({'T1':i})
        return out
#     
#     for i in range(n_iterations):
#         buildTemplateIteration = antsRegistrationTemplateBuildSingleIterationWF('iteration%d'%(i+1))
#         BeginANTS = buildTemplateIteration.get_node("BeginANTS")
#         BeginANTS.inputs.num_threads = 1
#         #BeginANTS.plugin_args = {'submit_specs': 'request_memory = 6000\nrequest_cpus = 32\n'}
# 
#         tbuilder.connect(prev_step_output[0], prev_step_output[1], buildTemplateIteration, 'inputspec.fixed_image')
# #        tbuilder.connect(sumMask,"output_average_image", BeginANTS, 'fixed_image_mask')
# #        tbuilder.connect(inputspec, "masks", BeginANTS, 'moving_image_mask')
#         buildTemplateIteration.inputs.inputspec.interpolationMapping = {'T1':'Linear'}
#         buildTemplateIteration.inputs.inputspec.registrationImageTypes = ['T1']
#         
#         tbuilder.connect(N4biasfield, ("output_image", make_dict), buildTemplateIteration, 'inputspec.ListOfImagesDictionaries')
#         
#         prev_step_output = (buildTemplateIteration, 'outputspec.template')
#         
#     BeginANTS=pe.Node(interface=Registration(), name = 'BeginANTS')
#     BeginANTS.inputs.dimension = 3
#     BeginANTS.inputs.output_transform_prefix = 'mni_tfm'
#     BeginANTS.inputs.transforms =               ["Affine",          "SyN"]
#     BeginANTS.inputs.transform_parameters =     [[0.9],             [0.25,3.0,0.0]]
#     BeginANTS.inputs.metric =                   ['Mattes',          'CC']
#     BeginANTS.inputs.metric_weight =            [1.0,               1.0]
#     BeginANTS.inputs.radius_or_number_of_bins = [32,                5]
#     BeginANTS.inputs.number_of_iterations = [[1000, 1000, 1000], [50, 35, 15]]
#     BeginANTS.inputs.use_histogram_matching =   [True,               True]
#     BeginANTS.inputs.use_estimate_learning_rate_once = [False,       False]
#     BeginANTS.inputs.shrink_factors =           [[3,2,1],            [3,2,1]]
#     BeginANTS.inputs.smoothing_sigmas =         [[3,2,0],            [3,2,0]]
#     BeginANTS.inputs.fixed_image = "/usr/share/fsl/data/standard/MNI152_T1_1mm_brain.nii.gz"
#     BeginANTS.inputs.num_threads = 1
#     
#     tbuilder.connect(prev_step_output[0], prev_step_output[1], BeginANTS, 'moving_image')
#     
#     merge_transforms = pe.Node(util.Merge(2), iterfield=['in1', 'in2'], name='merge_transforms')
#     tbuilder.connect(buildTemplateIteration, 'BeginANTS.forward_transforms', merge_transforms, 'in1')
#     tbuilder.connect(BeginANTS, 'forward_transforms', merge_transforms, 'in2')
#     merge_flags = pe.Node(util.Merge(2), iterfield=['in1', 'in2'], name='merge_flags')
#     tbuilder.connect(buildTemplateIteration, 'BeginANTS.forward_invert_flags', merge_flags, 'in1')
#     tbuilder.connect(BeginANTS, 'forward_invert_flags', merge_flags, 'in2')
#     
#     
#     wimtdeformed = pe.MapNode(interface = ApplyTransforms(),
#                      iterfield=['transforms','invert_transform_flags','input_image'],
#                      name ='wimtdeformed')
#     wimtdeformed.inputs.interpolation = 'Linear'
#     wimtdeformed.inputs.reference_image = "/usr/share/fsl/data/standard/MNI152_T1_1mm_brain.nii.gz"
#     wimtdeformed.inputs.default_value = 0
#     tbuilder.connect(merge_transforms,'out',wimtdeformed,'transforms')
#     tbuilder.connect(merge_flags,'out',wimtdeformed,'invert_transform_flags')
#     tbuilder.connect(N4biasfield, "output_image", wimtdeformed, 'input_image')
    
    buildTemplateIteration = antsRegistrationTemplateBuildSingleIterationWF('direct_to_MNI')
    BeginANTS = buildTemplateIteration.get_node("BeginANTS")
    BeginANTS.inputs.num_threads = 1
    buildTemplateIteration.inputs.inputspec.fixed_image = "/usr/share/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz"
    buildTemplateIteration.inputs.inputspec.interpolationMapping = {'T1':'Linear'}
    buildTemplateIteration.inputs.inputspec.registrationImageTypes = ['T1']
    tbuilder.connect(N4biasfield, ("output_image", make_dict), buildTemplateIteration, 'inputspec.ListOfImagesDictionaries')
    
        
    return tbuilder

if __name__ == '__main__':
    wf = pe.Workflow(name="main_workflow")
    wf.base_dir = os.path.join(workingdir, "ants_template")
    wf.config['execution']['crashdump_dir'] = wf.base_dir + "/crash_files"
      
    datagrabber = pe.MapNode(nio.FreeSurferSource(), 
                          name="datagrabber",
                          overwrite=False,
                          iterfield=['subject_id'])
    datagrabber.inputs.subjects_dir = freesurferdir
    datagrabber.inputs.subject_id = subjects
    
    threshold = pe.MapNode(fs.Binarize(min=0.5, out_type='nii.gz', dilate = 1),
                           iterfield=['in_file'],
                           name='threshold')
    
    def get_aparc_aseg(files):
        out_l = []
        for l in files:
            for name in l:
                if 'aparc+aseg' in name:
                    out_l.append(name)
                    break
        if out_l:
            return out_l
        else:
            raise ValueError('aparc+aseg.mgz not found')
    
    wf.connect([(datagrabber, threshold, [(('aparc_aseg', get_aparc_aseg), 'in_file')])])
    
    mask = pe.MapNode(fs.ApplyMask(out_file='brain.nii.gz'), iterfield=["in_file", 'mask_file'],  name="mask")
    wf.connect([(datagrabber, mask, [('orig', 'in_file')]),
                (threshold, mask, [('binary_file', 'mask_file')])])
    
    template_wf = create_custom_template()
    
    wf.connect(mask, "out_file", template_wf, "inputspec.t1_volumes")
    #wf.connect(threshold, "binary_file", template_wf, "inputspec.masks")
    
    tr_infosource = pe.Node(util.IdentityInterface(fields=['tr']), name="tr_infosource")
    tr_infosource.iterables = ("tr", ["645", "1400", "2500"])
    
    datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id', 'tr'], outfields=['func2anat_transform', 'epi_mask']), name="datagrabber2", iterfield=['subject_id'])
    datagrabber.inputs.base_directory = os.path.join(resultsdir,'volumes')
    datagrabber.inputs.template = '%s/_subject_id_%s/_tr_%s/%s*/*%s*.%s'
    datagrabber.inputs.template_args['func2anat_transform'] = [['func2anat_transform','subject_id', 'tr', '', 'tshift_bbreg', 'mat']]
    datagrabber.inputs.template_args['epi_mask'] = [['epi_mask','subject_id', 'tr', '', '', 'nii']]
    datagrabber.inputs.sort_filelist = True
    datagrabber.inputs.subject_id = subjects
    wf.connect(tr_infosource, "tr", datagrabber, "tr")
    
    timeseries_datagrabber = pe.Node(nio.DataGrabber(infields=['subject_id', 'tr'], outfields=['preprocessed_epi']), name="timeseries_datagrabber", iterfield=['subject_id'])
    timeseries_datagrabber.inputs.base_directory = os.path.join(resultsdir,'volumes')
    timeseries_datagrabber.inputs.template = 'preprocessed_resting/_subject_id_%s/_tr_%s/_selector_False.False.False.False.False.False/_fwhm_5/_highpass_freq_-1_lowpass_freq_-1/_bandpass_filter0/*.nii.gz'
    timeseries_datagrabber.inputs.template_args['preprocessed_epi'] = [['subject_id', 'tr']]
    timeseries_datagrabber.inputs.sort_filelist = True
    timeseries_datagrabber.inputs.subject_id = subjects
    wf.connect(tr_infosource, "tr", timeseries_datagrabber, "tr")
    
    func2anat_fsl2itk = pe.MapNode(c3.C3dAffineTool(), name="func2anat_fsl2itk", iterfield=["transform_file", "source_file", "reference_file"])
    func2anat_fsl2itk.inputs.itk_transform = True
    func2anat_fsl2itk.inputs.fsl2ras = True
    wf.connect(datagrabber, "func2anat_transform", func2anat_fsl2itk, "transform_file")
    wf.connect(datagrabber, "epi_mask", func2anat_fsl2itk, "source_file")
    wf.connect(mask, "out_file", func2anat_fsl2itk, "reference_file")
    
    collect_transforms = pe.MapNode(
        util.Merge(2),
        name='collect_transforms2', iterfield=["in1", "in2"])
    wf.connect(func2anat_fsl2itk, "itk_transform", collect_transforms, "in1")
    wf.connect(template_wf, "antsRegistrationTemplateBuildSingleIterationWF_direct_to_MNI.BeginANTS.forward_transforms", collect_transforms, "in2")

    def invert_list(l):
        reversed(l)
    
    timeseries2std = pe.MapNode(ants.WarpTimeSeriesImageMultiTransform(dimension=4), name="timeseries2std", iterfield=["input_image", "transformation_series"])
    timeseries2std.inputs.reference_image = "/usr/share/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz"
    #timeseries2std.inputs.num_threads = 1
    wf.connect(timeseries_datagrabber, "preprocessed_epi", timeseries2std, "input_image")
    wf.connect(collect_transforms, "out", timeseries2std, "transformation_series")
    #wf.connect(mask, "out_file", timeseries2std, "reference_image")
    
    wf.write_graph()
    wf.run(plugin="Condor")
