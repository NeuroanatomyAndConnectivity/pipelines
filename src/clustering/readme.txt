*HOW TO*

:Objectives:
	0) Preprocessing into surface data 
            [see chrisfilo's 'pipelines' documentation]
	1) Clustering the region of interest
	2) Visualizing the clusters

:Package Dependencies:
	* Nipype
    * Nibabel
    * Freesurfer
    * FSL
    * AFNI
    * Pysurfer

:Input Expectations:
	* Surface data from preprocessing step
        file system organization: [results folder]/volumes/sxfmout/[session]/[subject_id]/[smoothing]/[hemisphere]/[file]
    * fsaverage directory from freesurfer

:variables.py:
    * analysis_subjects is a list of all subject IDs.
    * analysis_sessions is a list of all sessions.
    * resultsdir is where preprocessed surface data are found.
    * freesurferdir is where the fsaverage4 folder is found.

    * labellist is a list of labels given by freesurfer which defines the region you would like to cluster. (currently set as prefrontal cortex)
    * hemisphere is a list of hemispheres to run
    * similarity_types is a list of similarity matrices you are interested in creating
    * cluster_types is a list of clustering methods you are interested in using
    * n_clusters is a list of the numbers of clusters you like to create. (currently only 7, but could be [7,8,9] for example)

:cluster_analysis.py:
    * From a command window run: 
        $ freesurfer        
        $ FSL
        $ AFNI
        $ python cluster_analysis.py
    * What happens is, the file directory becomes organized by the variables you inputed, 
      the data is then grabbed to the working directory, 
      it creates a mask for the prefrontal area (or whatever ROI you supply), 
      then the similarity matrices are made using similarity.py, 
      and then they are clustered using clustered.py. 
      After this, the results are dumped in the results folder.
    * It's not failproof, so if/when there are problems, please report on github or email me.

:Output Expectations:
    * In a new folder called 'clustered', you will find nifti-1 files with a cluster assignment for every vertex on the brain surface.

:Visualization:
    * From command window run 
        $ pysurfer fsaverage4 lh inflated
    * type: 
        >>> run visualization.py
    * Input one of two things:
        >>> add_cluster([location of niftifile],[hemisphere])
        >>> find_cluster([subject_id],[hemisphere],[similarity matrix type],[cluster type],[# of clusters],[session #])
