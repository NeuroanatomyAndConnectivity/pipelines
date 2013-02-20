import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio
import nipype.interfaces.ants as ants
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.fsl as fsl
from nipype.workflows.smri.ants.antsRegistrationBuildTemplate import antsRegistrationTemplateBuildSingleIterationWF
import os
from variables import workingdir, freesurferdir, subjects


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
    
    initAvg = pe.Node(interface=ants.AverageImages(), name ='initAvg')
    initAvg.inputs.dimension = 3
    initAvg.inputs.normalize = True

    tbuilder.connect(N4biasfield, "output_image", initAvg, "images")
    
#    sumMask = pe.Node(interface=ants.AverageImages(), name ='sumMask')
#    sumMask.inputs.dimension = 3
#    sumMask.inputs.normalize = False

#    tbuilder.connect(inputspec, "masks", sumMask, "images")
    
    prev_step_output = (initAvg, 'output_average_image')
    
    def make_dict(l):
        out = []
        for i in l:
            out.append({'T1':i})
        return out
    
    for i in range(n_iterations):
        buildTemplateIteration = antsRegistrationTemplateBuildSingleIterationWF('iteration%d'%(i+1))
        BeginANTS = buildTemplateIteration.get_node("BeginANTS")
        BeginANTS.inputs.num_threads = 1
        #BeginANTS.plugin_args = {'submit_specs': 'request_memory = 6000\nrequest_cpus = 32\n'}

        tbuilder.connect(prev_step_output[0], prev_step_output[1], buildTemplateIteration, 'inputspec.fixed_image')
#        tbuilder.connect(sumMask,"output_average_image", BeginANTS, 'fixed_image_mask')
#        tbuilder.connect(inputspec, "masks", BeginANTS, 'moving_image_mask')
        buildTemplateIteration.inputs.inputspec.interpolationMapping = {'T1':'Linear'}
        buildTemplateIteration.inputs.inputspec.registrationImageTypes = ['T1']
        
        tbuilder.connect(N4biasfield, ("output_image", make_dict), buildTemplateIteration, 'inputspec.ListOfImagesDictionaries')
        
        prev_step_output = (buildTemplateIteration, 'outputspec.template')
        
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
    
    wf.write_graph()
    wf.run(plugin="Condor")
