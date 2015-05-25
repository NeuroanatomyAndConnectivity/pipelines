#!/bin/bash

sublist=$1
srcdir='/scr/ilz2/LEMON_LSD/'

while read sub
do

    cd /afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/

    if [ -d probands/${sub}/ ] ; then
	echo "${sub} exists"
    
    else
	# create new proband
	echo "creating newvp ${sub}"
	newvp2 -p mar004 -c mar004 -o ${sub}
	# create freesurfer directory and symlink
	mkdir probands/${sub}/freesurfer/
	if [ -h freesurfer/$sub ] ; then
		echo "symlink freesurfer/${sub} exists"
	else
		echo "creating symlink freesurfer/${sub}"
		ln -s /afs/cbs.mpg.de/projects/mar004_lsd-lemon-preproc/probands/${sub}/freesurfer/ freesurfer/${sub}
	fi
	# copy files from ilz2
	echo "copying resting files ${sub}"
	cp -r ${srcdir}/${sub}/nifti/ probands/${sub}/nifti/
	cp -r ${srcdir}/${sub}/preprocessed/ probands/${sub}/preprocessed/
	echo "copying freesurfer files ${sub}"
	cp -r ${srcdir}/freesurfer/${sub}/* freesurfer/${sub}/
	echo "${sub} done"

    fi

done < $sublist


