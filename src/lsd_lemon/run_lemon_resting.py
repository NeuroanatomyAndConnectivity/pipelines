from lemon_resting import create_lemon_resting
import sys

'''
Meta script to run lemon resting state preprocessing
---------------------------------------------------
Can run in two modes:
python run_lemon_resting.py s {subject_id}
python run_lemon_resting.py f {text file containing list of subjects}
'''

mode=sys.argv[1]

if mode == 's':
    subjects=[sys.argv[2]]
elif mode == 'f':
    with open(sys.argv[2], 'r') as f:
        subjects = [line.strip() for line in f]

for subject in subjects:
    
    print 'Running subject '+subject

    working_dir = '/scr/ilz2/LEMON_LSD/working_dir_lemon/'+subject+'/' 
    data_dir = '/scr/ilz2/LEMON_LSD/'+subject+'/'             
    freesurfer_dir = '/scr/ilz2/LEMON_LSD/freesurfer/'
    lemon_dir = '/scr/ilz2/LEMON_LSD/'+subject+'/preprocessed/lemon_resting/'
    echo_space=0.00067 #in sec
    te_diff=2.46 #in ms
    epi_resolution = 2.3
    TR=1.4
    highpass=0.01
    lowpass=0.1
    vol_to_remove = 5
    pe_dir = 'y-'

    create_lemon_resting(subject=subject, working_dir=working_dir, data_dir=data_dir, 
                      freesurfer_dir=freesurfer_dir, out_dir=lemon_dir, 
                      vol_to_remove=vol_to_remove, TR=TR, 
                      epi_resolution=epi_resolution, highpass=highpass, 
                      lowpass=lowpass,echo_space=echo_space, te_diff=te_diff, 
                      pe_dir=pe_dir)