'''
Created on Sep 3, 2013

@author: kanaan
'''
'''
Created on Aug 6, 2013

@author: kanaan
'''
#!/usr/bin/env python
from nipype.interfaces.ants.registration import ANTS
"""
=============================================
Diffusion MRI Probabiltic tractography on NKI_enhanced.

This script uses FSL and MRTRIX algorithms to generate probabilstic tracts, tract density images
and  a 3D trackvis file of NKI_enhanced data.
=============================================

Packages and Data Setup
=======================
Import necessary modules from nipype.
"""

import nipype.interfaces.io as nio  # Data i/o
import nipype.interfaces.utility as util  # utility
import nipype.pipeline.engine as pe  # pypeline engine
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs  # freesurfer
import nipype.interfaces.mrtrix as mrtrix
import nipype.algorithms.misc as misc
import nipype.interfaces.cmtk as cmtk
import nipype.interfaces.dipy as dipy
import nipype.interfaces.ants as ants
import inspect
import os, os.path as op  # system functions
from nipype.workflows.dmri.fsl.dti import create_eddy_correct_pipeline
from nipype.workflows.dmri.camino.connectivity_mapping import select_aparc_annot
from nipype.utils.misc import package_check
import warnings
from nipype.workflows.dmri.connectivity.nx import create_networkx_pipeline, create_cmats_to_csv_pipeline
from nipype.workflows.smri.freesurfer import create_tessellation_flow

fsl.FSLCommand.set_default_output_type("NIFTI")


"""
Point to the freesurfer subjects directory (Recon-all must have been run on the subjects)
"""

subjects_dir = op.abspath(op.join(op.curdir, './freesurfer'))
fs.FSCommand.set_default_subjects_dir(subjects_dir)
fsl.FSLCommand.set_default_output_type('NIFTI')

fs_dir = os.environ['FREESURFER_HOME']
lookup_file = op.join(fs_dir, 'FreeSurferColorLUT.txt')

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Point to the folder containing the dwi, bvec and bval. All have to be in FSL format.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

data_dir = op.abspath(op.join(op.curdir, 'DTI_DIR'))
subject_list = ['0106057']

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Use infosource node to loop through the subject list and define the input files.
For our purposes, these are the dwi image, b vectors, and b values.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']), name="infosource")
infosource.iterables = ('subject_id', subject_list)

info = dict(dwi=[['subject_id', '*.nii']],
            bvecs=[['subject_id', '*.bvec']],
            bvals=[['subject_id', '*.bval']])

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Define a function that thresholds the bvals and zero's the 'near zero' B images.
This is a correction for the NKI DWI data. The Bval file has nine 'near zero' B images.
If this is not corrected, MRTRIX does not read these images as B0's introducing various
errors throughout the processing
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def threshold_bval(in_file, thr):
    import numpy as np
    import os
    value = np.genfromtxt(in_file)
    value[value < thr] = 0
    out_file = 'thresholded_%s.bval' % thr
    np.savetxt(out_file, value, delimiter=' ')
    return os.path.abspath(out_file)


from nipype.interfaces.utility import Function
threshold_b0 = pe.Node (name='threshold_b0',
                        interface=Function (input_names=['in_file', 'thr'],
                                              output_names=['out_file'],
                                              function=threshold_bval))
threshold_b0.inputs.thr = 100

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Use datasource node to perform the actual data grabbing.
Templates for the associated images are used to obtain the correct images.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=info.keys()),
                     name='datasource')

datasource.inputs.template = "%s/DTI_mx_137/%s"
datasource.inputs.base_directory = data_dir
datasource.inputs.template_args = info
datasource.inputs.sort_filelist = True

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
The input node and Freesurfer sources declared here will be the main
conduits for the raw data to the rest of the processing pipeline.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

inputnode = pe.Node(interface=util.IdentityInterface(fields=["subject_id", "dwi", "bvecs", "bvals", "subjects_dir"]), name="inputnode")
inputnode.inputs.subjects_dir = subjects_dir

FreeSurferSource = pe.Node(interface=nio.FreeSurferSource(), name='FreeSurferSource')

'''
===============================================================================
 Creating the workflow's nodes

===============================================================================
Conversion nodes
--------------------------------------------------------
Conversion operations are required to obtain NIFTI files from the FreesurferSource for each subject.
Nodes are used to convert the following:

    * Original structural image to NIFTI
'''

# mri_convert_Brain = pe.Node(interface=fs.MRIConvert(), name='mri_convert_Brain')
# mri_convert_Brain.inputs.out_type = 'nii'

'''
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Diffusion processing nodes
--------------------------

MRTRIX ENCODING
Convert FSL formt files bvecs and bvals into single encoding file for MRTrix
'''

fsl2mrtrix = pe.Node(interface=mrtrix.FSL2MRTrix(), name='fsl2mrtrix')
fsl2mrtrix.inputs.invert_x = True

"""
EDDY CURRENT CORRECTION
Correct for distortions induced by eddy currents before fitting the tensors.
The first image  is used as a reference for which to warp the others.
"""

eddycorrect = create_eddy_correct_pipeline(name='eddycorrect')
eddycorrect.inputs.inputnode.ref_num = 1

"""
TENSOR FITTING
Tensors are fitted to each voxel in the diffusion-weighted image and from these three maps are created:
    * Major eigenvector in each voxel
    * Apparent diffusion coefficient
    * Fractional anisotropy
"""

dwi2tensor = pe.Node(interface=mrtrix.DWI2Tensor(), name='dwi2tensor')
tensor2vector = pe.Node(interface=mrtrix.Tensor2Vector(), name='tensor2vector')
tensor2adc = pe.Node(interface=mrtrix.Tensor2ApparentDiffusion(), name='tensor2adc')
tensor2fa = pe.Node(interface=mrtrix.Tensor2FractionalAnisotropy(), name='tensor2fa')

"""
B0_MASK
This block creates the rough brain mask with two erosion steps. The mask will be used to generate an Single fiber voxel mask
for the estimation of the response function and a white matter mask which will serve as a seed for tractography.

"""
bet = pe.Node(interface=fsl.BET(mask=True), name='mask_b0')
erode_mask_firstpass = pe.Node(interface=fsl.maths.ErodeImage(), name='erode_b0mask_firstpass')
erode_mask_secondpass = pe.Node(interface=fsl.maths.ErodeImage(), name='erode_b0mask_secondpass')
FA_mif2nii = pe.Node(interface=mrtrix.MRConvert(), name='FA_mif2nii')
FA_mif2nii.inputs.extension = 'nii'

"""
Non-linear transformation of Fa map onto T1. This will generate a warp field that will be inverted to warp full t1 onto FA.


1- Convert ribbon, T1 freesurfer outputs to nii
2- Mask T1 with ribbon to extract the brain and get rid of the of the CB and BS.
3- Mask FA with eroded B0 mask
4- T1 --> FA ---- Register ribbon masked T1 onto B0 masked FA with 6DOFs, cross corr.
5- Close holes in T1_2_FA_6DOF (-dil -ero)
6- Mask original FA map with 6DOF FA registered,closed wholes T1.
7- Eroded FA -ero with default-kbox 3x3x3
8- Non-linearly transform t1, wm mask created from ribbon
"""
# convert t1and ribbon to nii
t1_nii = pe.Node(interface=fs.MRIConvert(), name='t1_nii')
t1_nii.inputs.out_type = 'nii'

ribbon_nii = pe.Node(interface=fs.MRIConvert(), name='ribbon_nii')
ribbon_nii.inputs.out_type = 'nii'

# mask t1 with ribbon
t1_ribbon_masked = pe.Node(interface=fsl.maths.ApplyMask(), name='t1_ribbon_masked')

# mask fa with b0 ... also erode it to use for estimation of response function
fa_B0_masked = pe.Node(interface=fsl.maths.ApplyMask(), name='fa_B0_masked')
fa_B0_masked_ero = pe.Node(interface=fsl.maths.MathsCommand(), name='fa_B0_masked_ero')
fa_B0_masked_ero.inputs.args = '-ero -ero '


# register T1_ribbon_masked to Fa_b0_masked
# flirt -in T1_masked.nii.gz -ref  fa_brain.nii.gz -out t12fa -omat t12fa.mat -bins 256 -cost corratio -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 6  -interp trilinear
flirt_t1masked_2_FAmasked = pe.Node(interface=fsl.FLIRT(), name='flirt_t1m_2_FAm')
flirt_t1masked_2_FAmasked.inputs.dof = 6
flirt_t1masked_2_FAmasked.inputs.cost_func = 'corratio'
flirt_t1masked_2_FAmasked.inputs.bins = 256
flirt_t1masked_2_FAmasked.inputs.interp = 'trilinear'
flirt_t1masked_2_FAmasked.inputs.searchr_x = [-90, 90]
flirt_t1masked_2_FAmasked.inputs.searchr_y = [-90, 90]
flirt_t1masked_2_FAmasked.inputs.searchr_z = [-90, 90]


# close holes in registered T12Fa
flirt_t1masked_2_FAmasked_closed_holes = pe.Node(interface=fsl.maths.MathsCommand(), name='flirt_t1m_2_FAm_close_holes')
flirt_t1masked_2_FAmasked_closed_holes.inputs.args = '-kernel sphere 3 -dilM -dilM  -ero -ero '


# # mask full fa with T12Fa_closed_holes
fa_ribbon_masked = pe.Node(interface=fsl.ApplyMask(), name='fa_ribbon_masked')
#
# # erode T1 masked FA
fa_ribbon_masked_ero = pe.Node(interface=fsl.ErodeImage(), name='fa_ribbon_masked_ero')

# Non-linearly transform FA_masked_ero to T1_ribbon_masked
# ANTS 3 -m PR[T1_masked.nii,FA_2_T1_6DOF.nii.gz,1,3] -i 5x5 -o FA_2_T1_ANTS.nii.gz -t SyN[0.25] -r Gauss[3,0]
ants_FA2T1m_2_T1_full = pe.Node (interface=ants.ANTS(), name='ants_fa_2_t1')
ants_FA2T1m_2_T1_full.inputs.dimension = 3
ants_FA2T1m_2_T1_full.inputs.output_transform_prefix = 'SY'
ants_FA2T1m_2_T1_full.inputs.metric = ['PR']
ants_FA2T1m_2_T1_full.inputs.radius = [3]
ants_FA2T1m_2_T1_full.inputs.metric_weight = [1.0]
ants_FA2T1m_2_T1_full.inputs.transformation_model = 'SyN'
ants_FA2T1m_2_T1_full.inputs.gradient_step_length = 0.25
ants_FA2T1m_2_T1_full.inputs.number_of_iterations = [ 5, 5]
ants_FA2T1m_2_T1_full.inputs.regularization = 'Gauss'
ants_FA2T1m_2_T1_full.inputs.regularization_gradient_field_sigma = 3
ants_FA2T1m_2_T1_full.inputs.regularization_deformation_field_sigma = 0

'''
Creation of masks for seeding
'''
# warp T1_masked to Fa_masked
warp_t1_2_fa = pe.Node (interface=ants.WarpImageMultiTransform(), name='warp_t1_2_fa')

# warp ribbon 2 fa
warp_ribbon_2_fa = pe.Node (interface=ants.WarpImageMultiTransform(), name='warp_ribbon_2_fa')
warp_ribbon_2_fa.inputs.use_nearest = True

# generate white matter mask and full brain mask from ribbon

ribbon_right_wm_41 = pe.Node(interface=fsl.maths.Threshold(), name='ribbon_right_wm_41')
ribbon_right_wm_41.inputs.thresh = 41
ribbon_right_wm_41.inputs.args = ' -uthr 41 -bin'

ribbon_right_gm_42 = pe.Node(interface=fsl.maths.Threshold(), name='ribbon_right_gm_42')
ribbon_right_gm_42.inputs.thresh = 42
ribbon_right_gm_42.inputs.args = ' -uthr 42 -bin'

ribbon_left_wm_2 = pe.Node(interface=fsl.maths.Threshold(), name='ribbon_left_wm_2')
ribbon_left_wm_2.inputs.thresh = 2
ribbon_left_wm_2.inputs.args = ' -uthr 2 -bin'

ribbon_left_gm_3 = pe.Node(interface=fsl.maths.Threshold(), name='ribbon_left_gm_3')
ribbon_left_gm_3.inputs.thresh = 3
ribbon_left_gm_3.inputs.args = ' -uthr 3 -bin'

ribbon_wm_mask = pe.Node(interface=fsl.maths.BinaryMaths(), name='ribbon_wm_mask')
ribbon_wm_mask.inputs.operation = 'add'

ribbon_wm_mask_ero = pe.Node(interface=fsl.maths.ErodeImage(), name='ribbon_wm_mask_ero')

# apply 0.2 threshold on  fa prob white matter tract
Atropos_FA_prob_wm_thr_02_bin = pe.Node(interface=fsl.maths.MathsCommand(), name='Atropos_FA_prob_wm_thr_02_bin')
Atropos_FA_prob_wm_thr_02_bin.inputs.args = '-thr 0.2 -bin'



# generate white matter mask from FA with 0.2 thresh
fa_ribbon_masked_ero_thresh02_bin = pe.Node(interface=fsl.maths.MathsCommand(), name='fa_ribbon_masked_ero_thresh02_bin')
fa_ribbon_masked_ero_thresh02_bin.inputs.args = '-thr 0.2 -bin '


# add fa_wm and ribbon_wm
fa_wm_holes_closed = pe.Node(interface=fsl.maths.BinaryMaths(), name='fa_wm_holes_closed')
fa_wm_holes_closed.inputs.operation = 'add'

# get rid of noisy voxels by eroding fa_t1_masked_ero again and multipling with fa_wm_closed_holes

fa_ribbon_masked_ero_ero = pe.Node(interface=fsl.maths.ErodeImage(), name='fa_ribbon_masked_ero_ero')
fa_wm_holes_closed_masked_fa_ribbon_masked_ero_ero = pe.Node(interface=fsl.ApplyMask(), name='fa_wm_holes_closed_mult_minus_noise')


fa_mask_closed_holes = pe.Node(interface=fsl.maths.MathsCommand(), name='fa_mask_closed_holes')
fa_mask_closed_holes.inputs.args = '-fillh'


# INTERFACE
# create tract seeding interface..
# ##this is  created by eroding and subtracting this from the non eroded final fa mask
fa_mask_closed_holes_ero = pe.Node(interface=fsl.maths.ErodeImage(), name='fa_mask_closed_holes_ero')
fa_mask_closed_holes_ero.inputs.kernel_shape = 'sphere'
fa_mask_closed_holes_ero.inputs.kernel_size = 2.5

interface_with_CSF = pe.Node(interface=fsl.maths.BinaryMaths(), name='interface')
interface_with_CSF.inputs.operation = 'sub'


####CSF mask extraction from B0

CSF_mask = pe.Node(interface=fsl.maths.MathsCommand(), name='CSF_mask')
CSF_mask.inputs.args = '-thrP 80 -bin -mul -1 -add 1'


#### Final White matter mask without CSF ---- fa_mask_closed_holes -mask CSF



# ## Final interface without CSF --- interface mask -mask csf



'''
Creation of Single fiber voxel mask for CSD
'''

# Create a singla fiber voxel mask
# this is done by thresholding the the FA MAP at 0.7

single_fiber_voxel_mask = pe.Node(interface=fsl.maths.MathsCommand(), name='single_fiber_voxel_mask')
single_fiber_voxel_mask.inputs.args = '-thr 0.7 -bin '

single_fiber_voxel_mask_mult_final_fa = pe.Node(interface=fsl.ApplyMask(), name='single_fiber_voxel_mask_mult_final_fa')
# single_fiber_voxel_mask_mult_final_fa.inputs.args = '-mul'

single_fiber_voxel_mask_mult_final_fa_mif = pe.Node(interface=mrtrix.MRConvert(), name='single_fiber_voxel_mask_mult_final_fa_mif')
single_fiber_voxel_mask_mult_final_fa_mif.inputs.extension = 'mif'


'''

MRTRIX starts here

'''

'''
 Estimation of the response function
 Estimation of the constrained spherical deconvolution depends on the estimate of the response function
 ::For damaged or pathological brains one should take care to lower the maximum harmonic order of these steps.
'''

estimateresponse = pe.Node(interface=mrtrix.EstimateResponseForSH(), name='estimateresponse')
estimateresponse.inputs.maximum_harmonic_order = 8

'''
Constrained spherical deconvolution fODF
'''

csdeconv = pe.Node(interface=mrtrix.ConstrainedSphericalDeconvolution(), name='csdeconv')
csdeconv.inputs.maximum_harmonic_order = 8


"""
Probabilistic tracking using the obtained fODF
Pay Attention to the number of tracts sampled from each voxel. Good values are usally in the millions.
"""

probCSDstreamtrack = pe.MapNode(interface=mrtrix.ProbabilisticSphericallyDeconvolutedStreamlineTrack(),
                             name='probCSDstreamtrack', iterfield=['seed_spec'])
probCSDstreamtrack.inputs.inputmodel = 'SD_PROB'
probCSDstreamtrack.inputs.desired_number_of_tracks = 2000

tracks2prob = pe.Node(interface=mrtrix.Tracks2Prob(), name='tracks2prob')
tracks2prob.inputs.colour = True

tracks2prob_nii = pe.Node(interface=mrtrix.MRConvert(), name='tracks2prob_nii')
tracks2prob_nii.inputs.extension = 'nii'

tck2trk = pe.Node(interface=mrtrix.MRTrix2TrackVis(), name='tck2trk')
trk2tdi = pe.Node(interface=dipy.TrackDensityMap(), name='trk2tdi')




'''
===============================================================================


Connecting the workflow

===============================================================================
Here we connect our processing pipeline.
Connecting the inputs, FreeSurfer nodes, and conversions
--------------------------------------------------------
'''

mapping = pe.Workflow(name='mapping')


"""
First, we connect the input node to the FreeSurfer input nodes.
"""

mapping.connect([(inputnode, FreeSurferSource, [("subjects_dir", "subjects_dir")])])
mapping.connect([(inputnode, FreeSurferSource, [("subject_id", "subject_id")])])

"""
Nifti conversion for subject's stripped brain image from Freesurfer:
"""

# mapping.connect([(FreeSurferSource, mri_convert_Brain, [('brain', 'in_file')])])


"""
Diffusion Processing
"""

mapping.connect([(inputnode, threshold_b0, [("bvals", "in_file")])])
mapping.connect([(threshold_b0, fsl2mrtrix, [("out_file", "bval_file")])])

mapping.connect([(inputnode, fsl2mrtrix, [("bvecs", "bvec_file")])])

mapping.connect([(inputnode, eddycorrect, [("dwi", "inputnode.in_file")])])
mapping.connect([(eddycorrect, dwi2tensor, [("outputnode.eddy_corrected", "in_file")])])
mapping.connect([(fsl2mrtrix, dwi2tensor, [("encoding_file", "encoding_file")])])
mapping.connect([(dwi2tensor, tensor2vector, [['tensor', 'in_file']]),
                       (dwi2tensor, tensor2adc, [['tensor', 'in_file']]),
                       (dwi2tensor, tensor2fa, [['tensor', 'in_file']])])

mapping.connect([(eddycorrect, bet, [("outputnode.eddy_corrected", "in_file")])])
mapping.connect([(bet, erode_mask_firstpass, [("mask_file", "in_file")])])
mapping.connect([(erode_mask_firstpass, erode_mask_secondpass, [("out_file", "in_file")])])
mapping.connect([(tensor2fa, FA_mif2nii, [("FA", "in_file")])])


"""
Non-linear transformation of FA map onto T1.
"""

# mask FA with B0
mapping.connect([(FA_mif2nii, fa_B0_masked, [("converted", "in_file")])])
mapping.connect([(erode_mask_firstpass, fa_B0_masked, [("out_file", "mask_file")])])


# convert T1 and ribbon
mapping.connect([(FreeSurferSource, t1_nii, [("T1", "in_file")])])


# define which ribbon to pick... lh.ribbon.mgz, rh.ribbon.mgz or ribbon.mgz
def pick_full_ribbon(ribbon_list):
    for f in ribbon_list:
        if f.endswith('lh.ribbon.mgz') or f.endswith('rh.ribbon.mgz'):
            continue
        else:
            return f

mapping.connect([(FreeSurferSource, ribbon_nii, [(("ribbon", pick_full_ribbon), "in_file")])])

# mask T1 with ribbon
mapping.connect([(t1_nii, t1_ribbon_masked , [("out_file", "in_file")])])
mapping.connect([(ribbon_nii, t1_ribbon_masked , [("out_file", "mask_file")])])

# register (rigidbody) T1_masked to FA_masked
mapping.connect([(t1_ribbon_masked, flirt_t1masked_2_FAmasked , [("out_file", "in_file")])])
mapping.connect([(fa_B0_masked, flirt_t1masked_2_FAmasked , [("out_file", "reference")])])
#
# close holes by dilating and eroding with default setting
mapping.connect([(flirt_t1masked_2_FAmasked, flirt_t1masked_2_FAmasked_closed_holes, [('out_file', 'in_file')])])

# mask full fa with flirt_t1masked_2_FAmasked_closed_holes
mapping.connect([(FA_mif2nii, fa_ribbon_masked , [("converted", "in_file")])])
mapping.connect([(flirt_t1masked_2_FAmasked_closed_holes, fa_ribbon_masked, [("out_file", "mask_file")])])

# # erode_masked_fa
mapping.connect([(fa_ribbon_masked, fa_ribbon_masked_ero , [("out_file", "in_file")])])

# # use ants to generate a deformation field FA to T1
mapping.connect([(fa_ribbon_masked_ero, ants_FA2T1m_2_T1_full, [('out_file', 'moving_image')])])
mapping.connect([(flirt_t1masked_2_FAmasked_closed_holes, ants_FA2T1m_2_T1_full, [('out_file', 'fixed_image')])])


# warp  T1_masked to fa_masked
mapping.connect([(flirt_t1masked_2_FAmasked_closed_holes, warp_t1_2_fa, [('out_file', 'input_image')])])
mapping.connect([(fa_ribbon_masked_ero, warp_t1_2_fa, [('out_file', 'reference_image')])])
mapping.connect([(ants_FA2T1m_2_T1_full, warp_t1_2_fa, [('inverse_warp_transform', 'transformation_series')])])

# warp ribbon_wm  to
mapping.connect([(ribbon_nii, warp_ribbon_2_fa, [('out_file', 'input_image')])])
mapping.connect([(fa_ribbon_masked_ero, warp_ribbon_2_fa, [('out_file', 'reference_image')])])
mapping.connect([(ants_FA2T1m_2_T1_full, warp_ribbon_2_fa, [('inverse_warp_transform', 'transformation_series')])])


"""
Create  seeding interface for tractography
"""
# extract 41wr,42gr,2wl,3gl

mapping.connect([(warp_ribbon_2_fa, ribbon_right_wm_41, [('output_image', 'in_file')])])
mapping.connect([(warp_ribbon_2_fa, ribbon_right_gm_42, [('output_image', 'in_file')])])
mapping.connect([(warp_ribbon_2_fa, ribbon_left_wm_2, [('output_image', 'in_file')])])
mapping.connect([(warp_ribbon_2_fa, ribbon_left_gm_3, [('output_image', 'in_file')])])

# create a white matter mask .. add41 and 2

mapping.connect([(ribbon_right_wm_41, ribbon_wm_mask, [('out_file', 'in_file')])])
mapping.connect([(ribbon_left_wm_2, ribbon_wm_mask, [('out_file', 'operand_file')])])
mapping.connect([(ribbon_wm_mask, ribbon_wm_mask_ero, [('out_file', 'in_file')])])
mapping.connect([(fa_ribbon_masked_ero, fa_ribbon_masked_ero_thresh02_bin, [('out_file', 'in_file')])])

# generate fa white matter with holes closed by adding eroded ribbon white matter mask
mapping.connect([(fa_ribbon_masked_ero_thresh02_bin, fa_wm_holes_closed, [('out_file', 'in_file')])])
mapping.connect([(ribbon_wm_mask_ero, fa_wm_holes_closed, [('out_file', 'operand_file')])])


# erode fa_masked_ero again to remove noise
mapping.connect([(fa_ribbon_masked_ero, fa_ribbon_masked_ero_ero , [("out_file", "in_file")])])

# remove noisy voxels
mapping.connect([(fa_wm_holes_closed, fa_wm_holes_closed_masked_fa_ribbon_masked_ero_ero , [("out_file", "in_file")])])
mapping.connect([(fa_ribbon_masked_ero_ero, fa_wm_holes_closed_masked_fa_ribbon_masked_ero_ero , [("out_file", "mask_file")])])

# final fa mask with holes closed by dilation and erosion
mapping.connect([(fa_wm_holes_closed_masked_fa_ribbon_masked_ero_ero, fa_final_mask , [("out_file", "in_file")])])

####CSF mask extraction from merged DWI
mapping.connect([(eddycorrect, CSF_mask, [('out_file', 'in_file')])])

#########       Interface         #########
# ## create tract seeding interface..  this is  created by eroding and subtracting this from the non eroded final fa mask
mapping.connect([(fa_mask_closed_holes, fa_mask_closed_holes_ero, [('out_file', 'in_file')])])

mapping.connect([(fa_mask_closed_holes, interface, [('out_file', 'in_file')])])
mapping.connect([(fa_final_mask_ero, interface, [('out_file', 'operand_file')])])








'''
Diffusion processing

'''
"""
Estimation of the response function
"""


mapping.connect([(fa_B0_masked, fa_B0_masked_ero, [('out_file', 'in_file')])])
mapping.connect([(fa_B0_masked_ero, single_fiber_voxel_mask, [('out_file', 'in_file')])])

mapping.connect([(single_fiber_voxel_mask, single_fiber_voxel_mask_mult_final_fa, [('out_file', 'in_file')])])
mapping.connect([(fa_final_mask, single_fiber_voxel_mask_mult_final_fa, [('out_file', 'mask_file')])])



mapping.connect([(single_fiber_voxel_mask_mult_final_fa, single_fiber_voxel_mask_mult_final_fa_mif, [('out_file', 'in_file')])])

mapping.connect([(eddycorrect, estimateresponse, [("outputnode.eddy_corrected", "in_file")])])
mapping.connect([(fsl2mrtrix, estimateresponse, [("encoding_file", "encoding_file")])])
mapping.connect([(single_fiber_voxel_mask_mult_final_fa_mif, estimateresponse, [("converted", "mask_image")])])

"""
Constrained spherical deconvolution
"""

mapping.connect([(eddycorrect, csdeconv, [("outputnode.eddy_corrected", "in_file")])])
mapping.connect([(fa_final_mask, csdeconv, [("out_file", "mask_image")])])
mapping.connect([(estimateresponse, csdeconv, [("response", "response_file")])])
mapping.connect([(fsl2mrtrix, csdeconv, [("encoding_file", "encoding_file")])])

single_fiber_voxel_mask_mult_final_fa


"""
Connect the tractography and compute visitation maps
"""
def get_voxel(in_file):
    import numpy as np
    import nibabel as nib
    file = nib.load(in_file)
    v = np.array(file.get_data())
    listoflists = []
    radius = 1.0
    for x, y, z in zip(*np.nonzero(v)):
        list = []
        list.append(x)
        list.append(y)
        list.append(z)
        matrix = file.get_affine()
        sub_matrix = matrix[0:3, 0:3]
        temp_coord = np.dot(list, sub_matrix)
        offset = matrix[0:3, 3:4]
        offset_transpose = np.transpose(offset)
        final_coord = np.add(offset_transpose, temp_coord)
        # print list
        # print final_coord
        final_element = []
        final_element.append(final_coord[0, 0])
        final_element.append(final_coord[0, 1])
        final_element.append(final_coord[0, 2])
        final_element.append(radius)
        # print final_element
        listoflists.append(final_element)
    return listoflists


mapping.connect([(fa_final_mask, probCSDstreamtrack, [("out_file", "mask_file")])])
mapping.connect([(interface, probCSDstreamtrack, [(('out_file', get_voxel), "seed_spec")])])
mapping.connect([(csdeconv, probCSDstreamtrack, [("spherical_harmonics_image", "in_file")])])

# mapping.connect([(probCSDstreamtrack, tracks2prob, [("tracked", "in_file")])])
# mapping.connect([(eddycorrect, tracks2prob, [("outputnode.eddy_corrected", "template_file")])])
# mapping.connect([(tracks2prob, tracks2prob_nii, [("tract_image", "in_file")])])




"""
Connect the tractography and compute the tract density image.
"""

######  grab coordinates from g/w matter interface

# def get_voxel():
#     import numpy as np
#     import nibabel as nib
#     file = nib.load()
#     v = np.array(file.get_data())
#     for x, y, z in zip(*np.nonzero(v)):
#         return "%d, %d, %d," % (x, y, z), '1'
#
# mapping.connect([(fa_final_mask, probCSDstreamtrack, [("out_file", "mask_file")])])
# mapping.connect([(interface, probCSDstreamtrack, [(get_voxel, "seed_file")])])
# mapping.connect([(csdeconv, probCSDstreamtrack, [("spherical_harmonics_image", "in_file")])])



# # define which ribbon to pick... lh.ribbon.mgz, rh.ribbon.mgz or ribbon.mgz
# def pick_full_ribbon(ribbon_list):
#     for f in ribbon_list:
#         if f.endswith('lh.ribbon.mgz') or f.endswith('rh.ribbon.mgz'):
#             continue
#         else:
#             return f
#
# mapping.connect([(FreeSurferSource, ribbon_nii, [(("ribbon", pick_full_ribbon), "in_file")])])


"""
Connect the tractography and compute the tract density image.
"""



"""
Create a higher-level workflow
------------------------------
Finally, we create another higher-level workflow to connect our mapping workflow with the info and datagrabbing nodes
declared at the beginning. Our tutorial is now extensible to any arbitrary number of subjects by simply adding
their names to the subject list and their data to the proper folders.
"""

connectivity = pe.Workflow(name="connectivity")

connectivity.base_dir = op.abspath('dmri_connectivity_final')
connectivity.connect([
                    (infosource, datasource, [('subject_id', 'subject_id')]),
                    (datasource, mapping, [('dwi', 'inputnode.dwi'),
                                               ('bvals', 'inputnode.bvals'),
                                               ('bvecs', 'inputnode.bvecs')
                                               ]),
        (infosource, mapping, [('subject_id', 'inputnode.subject_id')])
                   ])

"""
The following functions run the whole workflow and produce a .dot and .png graph of the processing pipeline.
"""

if __name__ == '__main__':
    # connectivity.run(updatehash=True)
    connectivity.run('Linear')
    connectivity.write_graph()
