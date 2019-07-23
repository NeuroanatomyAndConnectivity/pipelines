from convert import create_conversion
import getpass
import pandas as pd
import sys

'''Meta script to run conversion
---------------------------------
Input is a spreadsheet with information on location, 
experiment labels and scan IDs in xnat.

Will ask for xnat credentials
'''

list_conversion=sys.argv[1]

xnat_user = raw_input('XNAT username: ')
xnat_pass = getpass.getpass('XNAT password: ')
xnat_server = 'https://xnat.cbs.mpg.de/xnat' 

lemon_project_id = 'LEMON'
lsd_project_id = 'LEMON_LSD'

df=pd.read_excel(list_conversion, 'Sheet1')
subjects=list(df['subject_id'])

lemonlist = []
lsdlist = []
mp2ragelist = []


for subject in subjects:

    # read information about scans to process   
    subject_id = str(subject)
    while len(subject_id) < 5:
        subject_id = '0'+subject_id
    
    mp2rage_scans=dict()
    mp2rage_folder='mp2rage.@nifti'
    lemon_scans=dict()
    lemon_folder = 'lemon_resting.@nifti'
    lsd_scans=dict()
    lsd_folder = 'lsd_resting.@nifti'
    
    mp2rage=str(df[df['subject_id']==subject].iloc[0]['mp2rage'])
    lemon=str(df[df['subject_id']==subject].iloc[0]['lemon'])
    lsd=str(df[df['subject_id']==subject].iloc[0]['lsd'])
    
    mp2rage_scans['inv1']=df[df['subject_id']==subject].iloc[0]['inv1']
    mp2rage_scans['inv2']=df[df['subject_id']==subject].iloc[0]['inv2']
    mp2rage_scans['uni']=df[df['subject_id']==subject].iloc[0]['uni']
    mp2rage_scans['div']=df[df['subject_id']==subject].iloc[0]['div']
    mp2rage_scans['t1map']=df[df['subject_id']==subject].iloc[0]['t1map']
    
    lemon_scans['fmap_mag'] = df[df['subject_id']==subject].iloc[0]['lemon_fmap_mag']
    lemon_scans['fmap_phase'] = df[df['subject_id']==subject].iloc[0]['lemon_fmap_phase']
    lemon_scans['se1'] = df[df['subject_id']==subject].iloc[0]['lemon_se1']
    lemon_scans['se1_inv'] = df[df['subject_id']==subject].iloc[0]['lemon_se1_inv']
    lemon_scans['rest'] = df[df['subject_id']==subject].iloc[0]['lemon_rest']
    lemon_scans['se2'] = df[df['subject_id']==subject].iloc[0]['lemon_se2']
    lemon_scans['se2_inv'] = df[df['subject_id']==subject].iloc[0]['lemon_se2_inv']
    
    lsd_scans['se1'] = df[df['subject_id']==subject].iloc[0]['lsd_se1']
    lsd_scans['se1_inv'] = df[df['subject_id']==subject].iloc[0]['lsd_se1_inv']
    lsd_scans['fmap1_mag'] = df[df['subject_id']==subject].iloc[0]['lsd_fmap1_mag']
    lsd_scans['fmap1_phase'] = df[df['subject_id']==subject].iloc[0]['lsd_fmap1_phase']
    lsd_scans['rest1a'] = df[df['subject_id']==subject].iloc[0]['lsd_rest1a']
    lsd_scans['rest1b'] = df[df['subject_id']==subject].iloc[0]['lsd_rest1b']
    lsd_scans['se2'] = df[df['subject_id']==subject].iloc[0]['lsd_se2']
    lsd_scans['se2_inv'] = df[df['subject_id']==subject].iloc[0]['lsd_se2_inv']
    lsd_scans['fmap2_mag'] = df[df['subject_id']==subject].iloc[0]['lsd_fmap2_mag']
    lsd_scans['fmap2_phase'] = df[df['subject_id']==subject].iloc[0]['lsd_fmap2_phase']
    lsd_scans['rest2a'] = df[df['subject_id']==subject].iloc[0]['lsd_rest2a']
    lsd_scans['rest2b'] = df[df['subject_id']==subject].iloc[0]['lsd_rest2b']

    # set directories 
    working_dir = '/scr/ilz2/LEMON_LSD/working_dir_conversion/'+subject_id+'/' 
    nifti_dir = '/scr/ilz2/LEMON_LSD/'+subject_id+'/nifti/'

    # run conversion
    if not lemon == 'nan':
        create_conversion(name='lemon_conversion', subject=subject_id, scans=lemon_scans,
                       working_dir=working_dir, out_dir=nifti_dir, folder=lemon_folder,
                       xnat_server=xnat_server, xnat_user=xnat_user, xnat_pass=xnat_pass, 
                       project_id=lemon_project_id, exp_id=lemon)
        
    if not lsd == 'nan':
        create_conversion(name='lsd_conversion', subject=subject_id, scans=lsd_scans,
                       working_dir=working_dir, out_dir=nifti_dir, folder=lsd_folder,
                       xnat_server=xnat_server, xnat_user=xnat_user, xnat_pass=xnat_pass, 
                       project_id=lsd_project_id, exp_id=lsd)
        
    if mp2rage =='lemon':
        create_conversion(name='mp2rage_conversion', subject=subject_id, scans=mp2rage_scans,
                       working_dir=working_dir, out_dir=nifti_dir, folder=mp2rage_folder,
                       xnat_server=xnat_server, xnat_user=xnat_user, xnat_pass=xnat_pass, 
                       project_id=lemon_project_id, exp_id=lemon)
        
    elif mp2rage == 'lsd':
        create_conversion(name='mp2rage_conversion', subject=subject_id, scans=mp2rage_scans,
                       working_dir=working_dir, out_dir=nifti_dir, folder=mp2rage_folder,
                       xnat_server=xnat_server, xnat_user=xnat_user, xnat_pass=xnat_pass, 
                       project_id=lsd_project_id, exp_id=lsd)