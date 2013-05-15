import re
import datetime
import numpy as np
from collections import defaultdict

f = open("/home/raid3/gorgolewski/Downloads/dicom_text_resting_state.txt")

f.readline()
f.readline()
days_ago = []
vox_sizes = []
missing = 0
for line in f:
    fields = line.split("|")
    latest_rest = None
    tr = None
    vox_size_x = None
    vox_size_y = None
    vox_size_z = None
    if len(fields) > 1 and "rest" in line.lower():
        dicom_desc = line.split("|")[1]
        for study in dicom_desc.split("InstitutionAddress"):
            if study:
                r = re.compile("sequenceDescription:(?P<seq_desc>[0-9a-zA-Z_]*)")
                a = r.search(study)
                
                if a and "rest" in a.group("seq_desc").lower() and not ("field" in a.group("seq_desc").lower()):
                    print a.group("seq_desc")
                    r = re.compile("sequenceStart:(?P<date>[0-9\-a-zA-Z]*)")
                    a = r.search(study)
                    print a.group("date")
                    d = datetime.datetime.strptime(a.group("date"), "%Y-%b-%d").date()

                    r = re.compile("repetitionTime:(?P<TR>[0-9]*)")
                    a = r.search(study)
                    print a.group("TR")
                    
                    r = re.compile("voxelSize:\<(?P<vox_size_x>[.0-9]*);(?P<vox_size_y>[0-9.]*);(?P<vox_size_z>[0-9.]*)")
                    a = r.search(study)
                    print a.group("vox_size_x"), a.group("vox_size_y"), a.group("vox_size_z")
                    if latest_rest:
                        if d > latest_rest:
                            latest_rest = d
                            vox_size_x = a.group("vox_size_x")
                            vox_size_y = a.group("vox_size_y")
                            vox_size_z = a.group("vox_size_z")
                    else:
                        latest_rest = d
                        vox_size_x = a.group("vox_size_x")
                        vox_size_y = a.group("vox_size_y")
                        vox_size_z = a.group("vox_size_z")
        if not latest_rest:
            print line
            break
        print "subject %s had it latest resting state scan %s ago"%(fields[0], str(datetime.date.today() - latest_rest))
        days_ago.append((datetime.date.today() - latest_rest).days)
        vox_sizes.append((vox_size_x, vox_size_y, vox_size_z))
    else:
        missing += 1
        
print missing
print days_ago
print np.median(np.array(days_ago))
print np.min(np.array(days_ago))
print np.max(np.array(days_ago))

print vox_sizes

d = defaultdict(int)
for word in vox_sizes:
    d[word] += 1

for k in d.keys():
    d[k] /= float(len(vox_sizes))
print d             
    

