from lsd_resting import create_lsd_resting
import sys

'''
Meta script to run lsd resting state preprocessing
-------------------------------------------------
Can run in two modes:
python run_lsd_resting.py s {subject_id}
python run_lsd_resting.py f {text file containing list of subjects}
'''

mode=sys.argv[1]

if mode == 's':
    subjects=[sys.argv[2]]
elif mode == 'f':
    with open(sys.argv[2], 'r') as f:
        subjects = [line.strip() for line in f]

for subject in subjects:
    
    print 'Running subject '+subject

    working_dir = '/scr/ilz2/LEMON_LSD/working_dir_lsd/'+subject+'/' 
    data_dir = '/scr/ilz2/LEMON_LSD/'+subject+'/'             
    freesurfer_dir = '/scr/ilz2/LEMON_LSD/freesurfer/'
    lsd_dir = '/scr/ilz2/LEMON_LSD/'+subject+'/preprocessed/lsd_resting/'
    echo_space=0.00067 #in sec
    te_diff=2.46 #in ms
    epi_resolution = 2.3
    TR=1.4
    highpass=0.01
    lowpass=0.1
    vol_to_remove = 5
    scans=['rest1a','rest1b','rest2a','rest2b']

    create_lsd_resting(subject=subject, working_dir=working_dir, out_dir=lsd_dir, 
                    freesurfer_dir=freesurfer_dir, data_dir=data_dir, 
                    echo_space=echo_space, te_diff=te_diff, scans=scans,
                    vol_to_remove=vol_to_remove, epi_resolution=epi_resolution,
                    TR=TR, highpass=highpass, lowpass=lowpass)