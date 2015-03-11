from structural_cbstools import create_structural
#from structural import create_structural
import sys

'''
Meta script to run structural preprocessing
------------------------------------------
Can run in two modes:
python run_structural.py s {subject_id}
python run_structural.py f {text file containing list of subjects}
'''

mode=sys.argv[1]

if mode == 's':
    subjects=[sys.argv[2]]
elif mode == 'f':
    with open(sys.argv[2], 'r') as f:
        subjects = [line.strip() for line in f]

for subject in subjects:
    
    print 'Running subject '+subject
    
    working_dir = '/scr/ilz2/LEMON_LSD/working_dir_struct/' +subject+'/' 
    data_dir = '/scr/ilz2/LEMON_LSD/'+subject+'/'
    out_dir = '/scr/ilz2/LEMON_LSD/'+subject+'/'
    freesurfer_dir = '/scr/ilz2/LEMON_LSD/freesurfer/' 
    standard_brain = '/usr/share/fsl/5.0/data/standard/MNI152_T1_1mm_brain.nii.gz'
    
    create_structural(subject=subject, working_dir=working_dir, data_dir=data_dir, 
                freesurfer_dir=freesurfer_dir, out_dir=out_dir,
                standard_brain=standard_brain)
    