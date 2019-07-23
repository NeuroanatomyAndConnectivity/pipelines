# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""

from nipype.interfaces.base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File, Directory
from nipype.utils.filemanip import split_filename
import os.path as op
from nipype.interfaces.traits_extension import isdefined


class Full2CompactTractInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='-i %s', mandatory=True, position=1, desc='in file')
    mask_file = File(exists=True, argstr='-m %s', mandatory=True, position=2, desc='white matter mask file')
    num_tracks =traits.Int(argstr="-t %s", mandatory=True, desc="number of streamlines used to create the probabilistic tract")
    use_float = traits.Bool(argstr="-f", mandatory=False, desc="use float representation to write tracts")
    verbose = traits.Bool(argstr="-v", mandatory=False, desc="use verbose output")
    nat_file = File(name_template="%s_compact_nat.v", keep_extension=False, argstr='-n %s', hash_files=False,
                    position= -2, desc='output normalized file in natural units', name_source=["in_file"])
    log_file = File(name_template="%s_compact_log.v", keep_extension=False, argstr='-l %s', hash_files=False,
                    position= -1, desc='output normalized file in logarithmic units', name_source=["in_file"])

class Full2CompactTractOutputSpec(TraitedSpec):
    nat_file = File(exists=True, desc='Output compact tract normalized in natural units')
    log_file = File(exists=True, desc='Output compact tract normalized in logarithmic units')

class Full2CompactTract(CommandLine):
    """
    Convert a vista image tract into a vista compact tract (single vector).

    Example
    -------

    >>> compact = Full2CompactTract()
    >>> compact.inputs.in_file = 'full.v'
    >>> compact.inputs.mask_file = 'mask.v'
    >>> compact.inputs.out_file = 'compact.v'
    >>> compact.run()                                       # doctest: +SKIP
    """

    _cmd = '/home/raid2/moreno/Code/hClustering/bin/full2compacttract/full2compacttract'
    input_spec=Full2CompactTractInputSpec
    output_spec=Full2CompactTractOutputSpec
    
    
    

class DistMatrixInputSpec(CommandLineInputSpec):
    roi_file = File(exists=True, argstr='-roi %s', mandatory=True, position=1, desc='seed tracts ID file')
    tract_dir = Directory(argstr='-tracd %s', mandatory=True, position=2, desc='tract directory')
    memory =traits.Int(argstr="-mem %s", mandatory=False, desc="memory to be used (in Gb)")
    threshold =traits.Float(argstr="-thr %s", mandatory=True, desc="threshold for tractogram values")
    parallel =traits.Int(argstr="-nth %s", mandatory=False, desc="number of parallel processors to use")
    verbose = traits.Bool(argstr="-v", mandatory=False, desc="use verbose output")
    out_file = File(name_template="%s_distmat.v", keep_extension=False, argstr='-out %s', hash_files=False,
                    position= -1, desc='output distance matrix file', name_source=["roi_file"])

class DistMatrixOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='distance matrix')

class DistMatrix(CommandLine):
    """
    Compute a square pairwise distance matrix .

    Example
    -------

    >>> distmat = DistMatrix()
    >>> distmat.inputs.roi_file = 'roi.txt'
    >>> distmat.inputs.tract_dir = 'trac_dir'
    >>> distmat.run()                                       # doctest: +SKIP
    """

    _cmd = '/home/raid2/moreno/Code/hClustering/bin/distBlocks3/distblocks3'
    input_spec=DistMatrixInputSpec
    output_spec=DistMatrixOutputSpec

   

class DistMatrixLatInputSpec(CommandLineInputSpec):
    roi_file_a = File(exists=True, argstr='-roia %s', mandatory=True, position=1, desc='seed tracts a ID file')
    roi_file_b = File(exists=True, argstr='-roib %s', mandatory=True, position=2, desc='seed tracts b ID file')
    tract_dir_a = Directory(argstr='-traca %s', mandatory=True, position=3, desc='tract a directory')
    tract_dir_b = Directory(argstr='-tracb %s', mandatory=True, position=4, desc='tract b directory')
    memory =traits.Int(argstr="-mem %s", mandatory=False, desc="memory to be used (in Gb)")
    threshold =traits.Float(argstr="-thr %s", mandatory=True, desc="threshold for tractogram values")
    parallel =traits.Int(argstr="-nth %s", mandatory=False, desc="number of parallel processors to use")
    verbose = traits.Bool(argstr="-v", mandatory=False, desc="use verbose output")
    out_file = File(name_template="%s_distmat.v", keep_extension=False, argstr='-out %s', hash_files=False,
                    position= -1, desc='output distance matrix file', name_source=["roi_file"])

class DistMatrixLatOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='distance matrix')

class DistMatrixLat(CommandLine):
    """
    compute a distance matrix between two sets.

    Example
    -------

    >>> distmat = DistMatrixLat()
    >>> distmat.inputs.roi_file_a = 'roi_a.txt'
    >>> distmat.inputs.roi_file_b = 'roi_b.txt'
    >>> distmat.inputs.tract_dir_a = 'trac_dir_a'
    >>> distmat.inputs.tract_dir_b = 'trac_dir_b'
    >>> distmat.run()                                       # doctest: +SKIP
    """

    _cmd = '/home/raid2/moreno/Code/hClustering/bin/distBlocks3_lat/distblocks3_lat'
    input_spec=DistMatrixLatInputSpec
    output_spec=DistMatrixLatOutputSpec
