HOW TO make your own personal CLUSTERS!
======

Dependencies
------
- [Nipype](http://nipy.sourceforge.net/nipype/)
- [Nibabel](http://nipy.org/nibabel/)
- [Freesurfer](http://surfer.nmr.mgh.harvard.edu/)
- [FSL](http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/)
- [AFNI](http://afni.nimh.nih.gov/afni/)
- [Pysurfer](http://pysurfer.github.io/)
- [BIPs](https://github.com/INCF/BrainImagingPipelines/blob/master/bips/workflows/gablab/wips/scripts/base.py)

Objectives
------
0) [Preprocessing into surface data](#preprocessing)

1) [Building a similarity matrix from timeseries data](#similarity)

2) [Clustering the region of interest](#clustering)

3) [Finding the winner-take-all consensus amongst a set of solutions](#consensus)

2) [Visualizing the clusters](#visualization)


Input
------
- all input should be nifti-1 (.nii or .nii.gz) format
- freesurfer recon_all should be run on all subjects. The fsaverage directory is mandatory.
- you can start with resting state data
- or if you have preprocessed data as a timeseries, you can start by building a similarity matrix
- or, if you already have a similarity matrix, you can start clustering
- you can take a group of clustered solutions and find a consensus solution among them

Output
------
- In a folder called 'clustered', you will find nifti-1 files with a cluster assignment label for every vertex on the brain surface.
- look at these files using pysurfer & visualization.py

Create your personal variables.py
------
[example](../clustering/variables.py "example variables script")
- Base Directories
 - workingdir is where in-progress pipelines will live. (Heavy disk usage here)
 - freesurferdir is where you keep freesurfer and fsaverage files.
 - niftidir is where you keep your raw nifti files.
 - dicomdir is where you keep you raw dicom files.

- Result Directories
 - preprocdir is where preprocessed data are found.
 - similaritydir is where similarity matrix data are found
 - clusterdir is where clustered maps are found
 - consensusdir is where consensus data are found

- Data Specific Info
 - subjects is a list of all subject IDs.
 - sessions is a list of all sessions.
 - hemisphere is a list of hemispheres to run

- Brain Regions of Interest
 - set volume *and/or* surface regions of interest, using freesurfer labels
  -(see [freesurfercolors!.txt](../clustering/clustering/freesurfercolors!.txt) for reference)
  - if you want the whole brain use an empty set [ ]
  - if you want none of the brain use [-1]

- Parameters for Analysis
 - similarity_types is a list of similarity matrices you are interested in creating
 - cluster_types is a list of clustering methods you are interested in using
 - n_clusters is a list of the numbers of clusters you like to create.
 - epsilon is the input for DBScan clustering

<a name="preprocessing"/>
rs_preprocessing_pipeline.py
------
[source code](../clustering/rs_preprocessing_pipeline.py "preprocessing pipeline") as modified from [BIPs]

<a name="similarity"/>
similarity_pipeline.py
------
[source code](../clustering/similarity_pipeline.py "similarity pipeline")

<a name="clustering"/>
clustering_pipeline.py
------
[source code](../clustering/clustering_pipeline.py "clustering pipeline")
- From a command window run:
```Shell
user:$ freesurfer        
user:$ FSL
user:$ AFNI
user:$ python cluster_analysis.py
```
- What happens is, the file directory becomes organized by the variables you inputed, 
      the data is then grabbed to the working directory, 
      it creates a mask for the prefrontal area (or whatever ROI you supply), 
      then the similarity matrices are made using similarity.py, 
      and then they are clustered using clustered.py. 
      After this, the results are dumped in the results folder.

<a name="consensus"/>
consensus_pipeline.py
------
[source code](../clustering/consensus_pipeline.py "consensus pipeline")


<a name="visualization"/>
visualization.py
------
[source code](../clustering/clustering/visualization.py "visualization code")
- From command window run Pysurfer
```Shell
$ pysurfer fsaverage4 lh inflated
```
- In the ipython interface:
```Python
run visualization.py
```
- Load the data:
```Python
import nibabel as nb
clustermap = nb.load('location/of/niftifile').get_data()
add_cluster(clustermap,'lh') #or 'rh' for hemisphere
```
