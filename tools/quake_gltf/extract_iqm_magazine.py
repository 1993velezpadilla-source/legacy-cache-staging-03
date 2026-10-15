#!/usr/bin/env python3
"""Generate generic rigid-part animation metadata for IQM without touching geometry.

2026 XZIEL contributors. GPL-2.0-or-later. Off-line, no runtime dependencies.
The profile is MODEL-SPECIFIC. Engine accepts the metadata on any IQM model.
Source MP40: Moony_State CC BY 4.0; do not claim original BO3 rig/animation.
Only self-contained connected geometry is selected; contiguous receiver stays put.
"""
from pathlib import Path
import struct
import json
import sys
from collections import defaultdict

# GLB-origin model coordinates, obtained from a real IQM geometry audit.
PROFILES={
  "mp40_moony_state":{
    "tip_x_min":0.270, "tip_x_max":0.340, "tip_y_abs_max":0.025,
    "tip_z_below":-0.12, "component_x_min":0.280, "component_x_max":0.340,
    "component_y_abs_max":0.042, "component_z_below":0.088,
    "component_z_bottom":-0.16,
    "pivot":[0.306,0.0,0.075],
    "distance_down":0.25, "distance_side":0.095, "left_dir":-1,
    "min_faces":650, "max_faces":1300
  }
}

def load_iqm(path):
    data=path.read_bytes()
    if len(data)<124 or data[:16]!=b"INTERQUAKEMODEL\0" or (
        struct.unpack_from("<I",data,16)[0]!=2 or
        struct.unpack_from("<I",data,20)[0]!=len(data)):
        raise ValueError("Unsupported IQM2 file")
    count_va,nv,ofs_va,nf,ofs_tris=struct.unpack_from("<5I",data,44)
    if count_va>32 or nv>250000 or nf>180000 or nf<1:
        raise ValueError("IQM unreasonable buffer sizes")
    offset=None
    if ofs_va+count_va*20>len(data):raise ValueError("bad IQM vertex attrs")
    for k in range(count_va):
        kind,flags,fmt,width,ptr=struct.unpack_from("<5I",data,ofs_va+20*k)
        if kind==0 and fmt==7 and width==3:offset=ptr
    if offset is None or offset+nv*12>len(data) or ofs_tris+nf*12>len(data):
        raise ValueError("Invalid IQM coordinate or triangle span")
    pos=[struct.unpack_from("<3f",data,offset+i*12) for i in range(nv)]
    tris=[struct.unpack_from("<3I",data,ofs_tris+i*12) for i in range(nf)]
    if any(ix>=nv for tri in tris for ix in tri):raise ValueError("Bad IQM vertex index")
    return pos,tris

def islands(positions,triangles):
    parent=list(range(len(triangles)))
    rank=[0]*len(triangles)
    def root(n):
        while parent[n]!=n:
            parent[n]=parent[parent[n]]
            n=parent[n]
        return n
    def join(i,j):
        i,j=root(i),root(j)
        if i==j:return
        if rank[i]<rank[j]:i,j=j,i
        parent[j]=i
        if rank[i]==rank[j]:rank[i]+=1
    seen={}
    for i,tri in enumerate(triangles):
        for n in tri:
            key=tuple(round(x,5) for x in positions[n])
            if key in seen:join(i,seen[key])
            else:seen[key]=i
    groups=defaultdict(list)
    for k in range(len(triangles)):
        groups[root(k)].append(k)
    return groups.values()

def select_mag(positions,triangles,profile):
    selected=[]
    bounds=[]
    for face_ids in islands(positions,triangles):
        ids={v for i in face_ids for v in triangles[i]}
        vertices=[positions[k] for k in ids]
        lo=[min(p[a] for p in vertices) for a in range(3)]
        hi=[max(p[a] for p in vertices) for a in range(3)]
        tip=(lo[0]>=profile["tip_x_min"] and hi[0]<=profile["tip_x_max"] and
             max(abs(lo[1]),abs(hi[1]))<profile["tip_y_abs_max"] and
             lo[2]<=profile["tip_z_below"])
        column=(lo[0]>=profile["component_x_min"] and
                hi[0]<=profile["component_x_max"] and
                max(abs(lo[1]),abs(hi[1]))<=profile["component_y_abs_max"] and
                lo[2]>=profile["component_z_bottom"] and
                hi[2]<=profile["component_z_below"])
        if tip or column:
            selected.extend(face_ids)
            bounds.append((len(face_ids),[round(x,5) for x in lo],
                           [round(x,5) for x in hi]))
    if not profile["min_faces"]<=len(selected)<=profile["max_faces"]:
        raise ValueError("Selected magazine has unexpected polygon count: "+str(len(selected)))
    return selected,bounds

def stage(input_file,output_file,profile_name):
    pos,tris=load_iqm(input_file)
    profile=PROFILES[profile_name]
    ids,pieces=select_mag(pos,tris,profile)
    mask=bytearray(len(tris))
    for n in ids:mask[n]=1
    # 8 magic, 4 version, 4 IQM triangle count, 6 floats: pivot3,
    # drop distance (model units), sideways distance, sign.
    blob=struct.pack("<8sII6f",b"XZIQPART",1,len(tris),*profile["pivot"],
                     profile["distance_down"],profile["distance_side"],
                     float(profile["left_dir"]))+mask
    output_file.parent.mkdir(parents=True,exist_ok=True)
    output_file.write_bytes(blob)
    info={"model":str(input_file),"triangles":len(tris),
          "magazine_triangles":len(ids),"magazine_islands":len(pieces),
          "geometry_unchanged":True,"part_bounds":pieces}
    print(json.dumps(info,indent=2))
    return info

if __name__=="__main__":
    if len(sys.argv)!=4:
        sys.exit("usage: extract_iqm_magazine.py <model.iqm> <model.iqmparts> <profile>")
    stage(Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3])
