#!/usr/bin/env python3
"""Generate a rigorously validated, per-face moving-magazine mask for IQM.

Reads the actual, unchanged MP40 IQM geometry; identifies disconnected
magazine surface components whose bounds reach the bottom of the gun.
The mask does not modify geometry or textures and moves only its 348
source triangles. Fail rather than animate a wrong weapon component.

File format: 8 bytes XIQMPART + LE u32 triangle_count + packed bitset
(bit i = 1 when triangle i belongs to the actual magazine).
"""
from pathlib import Path
import json
import struct
import sys

MAGIC=b"XIQMPART"

def extract(path):
    raw=path.read_bytes()
    if len(raw)<124 or raw[:16]!=b"INTERQUAKEMODEL\0":
        raise ValueError("Expected IQM2 header")
    u=lambda at: struct.unpack_from("<I",raw,at)[0]
    n=u(48); nf=u(56); no=u(44); vao=u(52); trio=u(60)
    if not(1<=n<=250000 and 1<=nf<=180000 and no<=32):
        raise ValueError("Invalid IQM geometry dimensions")
    positions=None
    for k in range(no):
        typ,flags,fmt,width,off=struct.unpack_from("<5I",raw,vao+20*k)
        if typ==0 and fmt==7 and width==3:
            if off+12*n>len(raw):raise ValueError("Truncated XYZ")
            positions=[struct.unpack_from("<3f",raw,off+12*i) for i in range(n)]
            break
    if positions is None:raise ValueError("Missing float3 POSITION")
    if trio+12*nf>len(raw):raise ValueError("Truncated triangles")
    triangles=[struct.unpack_from("<3I",raw,trio+12*i) for i in range(nf)]
    if any(idx>=n for face in triangles for idx in face):
        raise ValueError("Triangle indices outside XYZ range")
    return positions,triangles

def mask_magazine(positions, triangles):
    n=len(positions)
    parent=list(range(n))
    rank=bytearray(n)
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]
            i=parent[i]
        return i
    def join(a,b):
        a=root(a);b=root(b)
        if a==b:return
        if rank[a]<rank[b]:a,b=b,a
        parent[b]=a
        if rank[a]==rank[b]:rank[a]+=1
    for a,b,c in triangles:
        join(a,b);join(a,c)
    comps={}
    for i,(a,b,c) in enumerate(triangles):
        r=root(a)
        comps.setdefault(r,[]).append(i)
    # The source MP40 has a distinct long magazine bottom at z=-0.146.
    # Derive bounds from the actual geometry; do NOT rely on material naming.
    lowest=min(p[2] for p in positions)
    bottom=[v for v in positions if v[2]<lowest+.010]
    if len(bottom)<12:raise ValueError("No bottom magazine geometry")
    bx0=min(v[0] for v in bottom)
    bx1=max(v[0] for v in bottom)
    if not 0.01<bx1-bx0<0.10:raise ValueError("Implausible magazine width")
    mag=[]
    for inds in comps.values():
        vertex_ids={idx for face_i in inds for idx in triangles[face_i]}
        vs=[positions[idx] for idx in vertex_ids]
        minx=min(v[0] for v in vs);maxx=max(v[0] for v in vs)
        minz=min(v[2] for v in vs)
        if minz < lowest+.055 and minx>=bx0-.015 and maxx<=bx1+.015:
            mag.extend(inds)
    mag.sort()
    if not 0.015<len(mag)/len(triangles)<0.04:
        raise ValueError("Ambiguous magazine segmentation fraction")
    if len(positions)==12628 and len(triangles)==14450 and len(mag)!=348:
        raise ValueError("Unexpected MP40 magazine triangle count; verify geometry manually")
    return mag,{"triangle_count":len(triangles),"magazine_triangles":len(mag),
                "bottom_z":lowest,"bottom_x":[bx0,bx1],
                "components_total":len(comps)}

def generate(inp, output):
    positions,faces=extract(inp)
    selected,info=mask_magazine(positions,faces)
    bits=bytearray((len(faces)+7)//8)
    for idx in selected:bits[idx//8]|=1<<(idx%8)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(MAGIC+struct.pack("<I",len(faces))+bits)
    assert sum(int(b).bit_count() for b in bits)==len(selected)
    print("XZIEL_ACTUAL_MP40_MOVABLE_MAGAZINE_MASK_GREEN")
    print(json.dumps(info,indent=2))
    return info

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: prepare_reload_parts.py <model.iqm> <model.iqmparts>")
    generate(Path(sys.argv[1]),Path(sys.argv[2]))
