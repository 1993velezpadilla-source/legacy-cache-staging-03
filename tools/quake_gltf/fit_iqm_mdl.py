#!/usr/bin/env python3
"""Compute a uniform IQM-to-legacy Quake MDL viewmodel alignment.

Matches real first-pose model extents from the *unmodified original MDL*;
does not decimate, reorient, or move a single IQM vertex on disk.
The runtime applies this reversible 3D matrix when drawing the IQM overlay.
"""
import json
import math
import struct
import sys
from pathlib import Path

def mdl_bbox(path):
    b=path.read_bytes()
    if len(b)<84 or b[:4]!=b"IDPO" or struct.unpack_from("<I",b,4)[0]!=6:
        raise ValueError("expected Quake MDL version 6")
    scale=struct.unpack_from("<3f",b,8)
    origin=struct.unpack_from("<3f",b,20)
    skins,w,h,verts,tris,frames=struct.unpack_from("<6I",b,48)
    if not (0<skins<32 and 0<w*h<=2048*2048 and 0<verts<20000 and 0<tris<40000 and frames>0):
        raise ValueError("unreasonable MDL sizes")
    pos=84
    for k in range(skins):
        if pos+4>len(b):raise ValueError("truncated skin type")
        typ=struct.unpack_from("<I",b,pos)[0];pos+=4
        if typ!=0:raise ValueError("grouped skins unsupported")
        pos+=w*h
    pos+=12*verts+16*tris
    if pos+28+verts*4>len(b):raise ValueError("missing first MDL frame")
    frametype=struct.unpack_from("<I",b,pos)[0];pos+=4
    if frametype!=0:raise ValueError("grouped first frame unsupported")
    pos+=24
    coords=[tuple(origin[i]+scale[i]*b[pos+4*k+i] for i in range(3)) for k in range(verts)]
    return [min(v[i] for v in coords) for i in range(3)], [max(v[i] for v in coords) for i in range(3)]

def iqm_bbox(path):
    b=path.read_bytes()
    if len(b)<124 or b[:16]!=b"INTERQUAKEMODEL\0":
        raise ValueError("expected IQM2")
    count,va_ofs,va_count=struct.unpack_from("<3I",b,48)  # vertices, attr offset, triangles? not used
    va_count=struct.unpack_from("<I",b,44)[0]
    if not (0<count<250001 and va_count<=32):raise ValueError("bad vertex count")
    for k in range(va_count):
        desc_off=va_ofs+20*k
        if desc_off+20>len(b):raise ValueError("bad vertex descriptor")
        typ,flags,fmt,width,offset=struct.unpack_from("<5I",b,desc_off)
        if typ==0 and fmt==7 and width==3:
            if offset+count*12>len(b):raise ValueError("bad vertex data")
            coords=[struct.unpack_from("<3f",b,offset+j*12) for j in range(count)]
            return [min(v[i] for v in coords) for i in range(3)], [max(v[i] for v in coords) for i in range(3)]
    raise ValueError("missing float POSITION")

def write_alignment(mdl,iqm,dest):
    amin,amax=mdl_bbox(mdl);bmin,bmax=iqm_bbox(iqm)
    original=[amax[i]-amin[i] for i in range(3)]
    modern=[bmax[i]-bmin[i] for i in range(3)]
    if min(modern)<1e-6 or min(original)<1e-6:
        raise ValueError("degenerate model bound")
    # Both Quake viewmodel and glTF->IQM MP40 have gun barrel X and height Z.
    # Use one uniform scale, preserving aspect ratios and high-poly geometry.
    scales=[original[0]/modern[0], original[2]/modern[2]]
    factor=sum(scales)/len(scales)
    if not 0.01<factor<1000 or any(not math.isfinite(v) for v in [factor]+original+modern):
        raise ValueError("implausible transform")
    offsets=[
       amin[0]-factor*bmin[0],
       (amin[1]+amax[1])/2-factor*(bmin[1]+bmax[1])/2,
       amin[2]-factor*bmin[2]
    ]
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(" ".join(f"{n:.9g}" for n in [factor]+offsets)+"\n")
    report={"original_mdl_min":amin,"original_mdl_max":amax,
            "iqm_min":bmin,"iqm_max":bmax,
            "iqm_scale":factor,"xyz_offset":offsets,"source_vertex_decimation":False}
    print(json.dumps(report,indent=2))
    return report

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: fit_iqm_mdl.py <viewmodel.mdl> <viewmodel.iqm> <viewmodel.iqmfit>")
    write_alignment(*map(Path,sys.argv[1:]))
