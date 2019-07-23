'''
Created on Oct 17, 2013

@author: moreno
'''

"""
threshold b values in bval file lower than thr to 0
"""
def script_tracking(subject_ID, chunk_nr, output_dir, tract_number,tract_step, is_left, use_sample=False):
    import numpy as np
    from subprocess import call
    import os.path as op
    import time 
    from dmri_pipe_aux import write_sequence_file



    if (is_left):
        hemi_string = 'lh'
        side_string = 'left'
    else:
        hemi_string = 'rh'
        side_string = 'right'
        
    seed_filename = output_dir+'/'+subject_ID+'/fa_masking/'+subject_ID+'_interface_'+side_string+'_mrtrix.txt'
    script_dir = output_dir+'/'+subject_ID+'/track_scripts/'
    chunk_dir=script_dir+hemi_string+'_chunks'
    seeds_dir=chunk_dir+"/seeds"
    call("mkdir "+script_dir, shell=True)
    call("mkdir "+chunk_dir, shell=True)
    call("mkdir "+seeds_dir, shell=True)
    
    if(is_left):
        call("mkdir "+output_dir+"/"+subject_ID+"/raw_tracts", shell=True)
        call("mkdir "+output_dir+"/"+subject_ID+"/compact_tracts", shell=True)
        call("mkdir "+output_dir+"/"+subject_ID+"/compact_tracts/nat", shell=True)
        call("mkdir "+output_dir+"/"+subject_ID+"/compact_tracts/log", shell=True)
        
    call("mkdir "+output_dir+"/"+subject_ID+"/raw_tracts/"+hemi_string, shell=True)
    call("mkdir "+output_dir+"/"+subject_ID+"/compact_tracts/nat/"+hemi_string, shell=True)
    call("mkdir "+output_dir+"/"+subject_ID+"/compact_tracts/log/"+hemi_string, shell=True)
    
    chunk_file_prefix=seeds_dir+'/chunk_'
    
    all_seeds = np.loadtxt(seed_filename, delimiter=' ')
    
    print("preparing for tracking of "+side_string+" hemisphere of subject "+subject_ID)

    final_seeds = []

    if(use_sample):
        maxsize=len(all_seeds)
        chunk_size=9
        for i in xrange(chunk_nr):
            this_chunk=[]
            for j in xrange(3):
                for k in xrange(3):
                    index=k+(1000*(j+(3*i)))
                    if (index >= maxsize):
                        break
                    this_seed=all_seeds[j*1000 + 1]
                    this_chunk.append(this_seed.tolist())
                    final_seeds.append(this_seed.tolist())
            submit_chunk=np.asarray(this_chunk)
            this_chunk_filename=chunk_file_prefix+str(i)+'.txt'
            np.savetxt(this_chunk_filename, submit_chunk, fmt='%f', delimiter=',')
    
    else:
        chunk_size = int(np.ceil(float(len(all_seeds))/chunk_nr))
        final_seeds=all_seeds.tolist()
        for i in xrange(chunk_nr):
            start_seed = i*chunk_size
            if (i==chunk_nr-1):
                end_seed = len(all_seeds)
            else:
                end_seed = (i+1)*chunk_size
            this_chunk = all_seeds[start_seed:end_seed]
            this_chunk_filename=chunk_file_prefix+str(i)+'.txt'
            np.savetxt(this_chunk_filename, this_chunk, fmt='%f', delimiter=',')
    
    out_sequence_filename=output_dir+"/"+subject_ID+"/compact_tracts/"+subject_ID + "_" + side_string + ".txt"
    write_sequence_file(final_seeds,out_sequence_filename)
    
    print("created "+str(chunk_nr)+" tracking chunks with "+str(chunk_size)+" seeds each")
    
    subject_line='SUBJECT="'+subject_ID+'"'
    seedxfile_line="SEEDS_PER_FILE="+str(chunk_size)
    hemi_line='HEMI="'+hemi_string+'"'
    trackcount_line='TRACK_COUNT="'+str(tract_number)+'"'
    trackcstep_line='STEP="'+str(tract_step)+'"'
    chunksdir_line='CHUNKS_DIR="'+chunk_dir+'"'
    outdir_line='OUTPUT_DIR="'+output_dir+'/'+subject_ID+'"'


    
    script_filename=chunk_dir+"/script_chunk"".sh"

    with open(script_filename, 'w+') as script_file:
        with open(output_dir+"/track_script_header.sh", "r") as header_file:
            script_file.write(header_file.read())
        script_file.write(subject_line+"\n")
        script_file.write(seedxfile_line+"\n")
        script_file.write(hemi_line+"\n")
        script_file.write(trackcount_line+"\n")
        script_file.write(trackcstep_line+"\n")
        script_file.write(chunksdir_line+"\n")
        script_file.write(outdir_line+"\n")

        with open(output_dir+"/track_script_body.sh", "r")as body_file:
            script_file.write(body_file.read())
            
            
    print("tracking script created in: "+ script_filename)

            
    submit_filename =  script_dir+subject_ID+"_"+hemi_string+"_tocondor.submit"        
    with open(submit_filename, "w") as submitter_file:
        submitter_file.write('executable = '+script_filename+'\n')
        submitter_file.write('getenv = True\nuniverse = vanilla\nrequest_memory = 500\nrequest_disk = 500000\nrequest_cpus = 1\nnotification = Error\n\n')
#        submitter_file.write('requirements = Machine == "kalifornien.cbs.mpg.de"\n\n')  
        for i in xrange(chunk_nr):
            submitter_file.write("arguments = "+str(i)+"\n")
            submitter_file.write("output = "+chunk_dir+"/logs/op_chunk_"+str(i)+".out\n")
            submitter_file.write("error = "+chunk_dir+"/logs/op_chunk_"+str(i)+".error\n")
            submitter_file.write("log = "+chunk_dir+"/logs/op_chunk_"+str(i)+".log\n")
            submitter_file.write("queue\n\n")
            
    print("condor submitter file created in: "+ submit_filename)

            
    call("chmod a+x "+script_filename, shell=True)
    call("mkdir "+chunk_dir+"/logs", shell=True)
    

    
    print("Submitting "+submit_filename+"...\n")
    call("condor_submit "+submit_filename, shell=True)
    
    
def trackwait(subject_ID, chunk_nr, output_dir):
    from subprocess import call
    import os.path as op
    import time 

    script_dir = output_dir+'/'+subject_ID+'/track_scripts/'

    
    print("Waiting for tracking scripts to finish...")
    still_running=True
    while(still_running):
        still_running=False
        for this_chunk in xrange(chunk_nr):
            success_log_filename_lh=script_dir+"lh_chunks/logs/"+subject_ID+"_lh_chunk_"+str(this_chunk)+".log"
            success_log_filename_rh=script_dir+"rh_chunks/logs/"+subject_ID+"_rh_chunk_"+str(this_chunk)+".log"
            if ( (not op.isfile(success_log_filename_lh)) or (not op.isfile(success_log_filename_rh)) ):
                still_running=True
                break
            #end if
        #end for
        time.sleep(60) 
    #end while
    call("gzip -f "+script_dir+"/[lr]h_chunks/logs/op_chunk_*.error", shell=True)
    print("All tracks finished! continuing workflow...\n")
#end if

                
    
                


    
    