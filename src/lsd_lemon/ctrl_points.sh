#!/bin/bash

# export SUBJECTS_DIR=/scr/jessica2/Schaare/LEMON/freesurfer
# cd $SUBJECTS_DIR/{subject}/tmp
# tmkedit {subject} orig.mgz  set and save control points
# ./ctrl_points.sh {subject}

cd $SUBJECTS_DIR/$1/mri
mkdir nu

mri_convert orig.mgz nu/nu0.mnc
cd nu
nu_correct -clobber nu0.mnc nu1.mnc
nu_correct -clobber nu1.mnc nu2.mnc
nu_correct -clobber nu2.mnc nu3.mnc
nu_correct -clobber nu3.mnc nu4.mnc
mri_convert nu4.mnc nu.mgz


cd ../

for i in {1..10};
do mri_normalize -sigma 10 -fonly ../tmp/control.dat ../mri/nu/nu.mgz ../mri/brain.mgz
cp ../mri/brain.mgz ../mri/T1.mgz
cp ../mri/brain.mgz ../mri/brain_mask.mgz

done

# then rerun recon-all (Alex:recon-all -autorecon2-cp -autorecon3 -subjid cp_before)
# see also http://freesurfer.net/fswiki/FsTutorial/ControlPoints_tktools
