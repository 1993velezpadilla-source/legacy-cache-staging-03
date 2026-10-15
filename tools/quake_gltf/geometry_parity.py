#!/usr/bin/env python3
"""Synthetic GLB->IQM geometry integrity: face normals, winding and total area.

This is NOT visual proof. It catches whole-mesh inverse winding/normal signs
and drastic triangle area changes that vertex/triangle counts miss.
Only verifies the generated single-primitive synthetic fixture.
"""
import json
import math
import struct
import sys
from pathlib import Path


def glb_payload(path):
    blob=path.read_bytes()
    if blob[:4]!=b"glTF" or struct.unpack_from("<I",blob,4)[0]!=2:
        raise ValueError("GLB2 required")
    pos=12
    doc=raw=None
    while pos+8<=len(blob):
        n,kind=struct.unpack_from("<II",blob,pos)
        pos+=8
        data=blob[pos:pos+n]
        if len(data)!=n: raise ValueError("truncated GLB")
        if kind==0x4E4F534A: doc=json.loads(data)
        if kind==0x004E4942: raw=data
        pos+=n
    if doc is None or raw is None: raise ValueError("missing chunks")
    primitive=doc["meshes"][0]["primitives"][0]
    def read(index):
        a=doc["accessors"][index]
        bv=doc["bufferViews"][a["bufferView"]]
        if "byteStride" in bv or a.get("sparse"): raise ValueError("strided/sparse source not supported")
        sizes={"VEC3":3,"SCALAR":1}
        n=sizes[a["type"]]
        typ={5125:("I",4),5126:("f",4)}[a["componentType"]]
        off=bv.get("byteOffset",0)+a.get("byteOffset",0)
        out=[]
        for i in range(a["count"]):
            at=off+i*n*typ[1]
            if at+n*typ[1]>len(raw): raise ValueError("GLB accessor out of bounds")
            out.append(struct.unpack_from("<"+str(n)+typ[0],raw,at))
        return out
    return read(primitive["attributes"]["POSITION"]),read(primitive["attributes"]["NORMAL"]),[
        e[0] for e in read(primitive["indices"])
    ]


def iqm_payload(path):
    b=path.read_bytes()
    if len(b)<124 or b[:16]!=b"INTERQUAKEMODEL\0":
        raise ValueError("IQM2 header missing")
    def u(pos):return struct.unpack_from("<I",b,pos)[0]
    if u(16)!=2 or u(20)!=len(b): raise ValueError("Bad IQM2 header")
    count,triangles=u(48),u(56)
    pos=normal=None
    va_offset=u(52)
    for i in range(u(44)):
        typ,flags,fmt,width,offset=struct.unpack_from("<5I",b,va_offset+i*20)
        if fmt==7 and width==3 and (typ==0 or typ==2):
            end=offset+count*12
            if end>len(b): raise ValueError("bad attribute")
            arr=[struct.unpack_from("<3f",b,offset+j*12) for j in range(count)]
            if typ==0:pos=arr
            else:normal=arr
    if pos is None or normal is None:raise ValueError("missing IQM position/normal")
    if u(60)+triangles*12>len(b):raise ValueError("bad triangle section")
    inds=list(struct.unpack_from("<"+str(triangles*3)+"I",b,u(60)))
    if any(i>=count for i in inds):raise ValueError("bad triangle index")
    return pos,normal,inds


def stats(points,normals,indices):
    if len(indices)%3:raise ValueError("non triangular")
    pos=neg=zero=0
    area=0.0
    for offset in range(0,len(indices),3):
        i,j,k=indices[offset:offset+3]
        a,b,c=points[i],points[j],points[k]
        u=[b[t]-a[t] for t in range(3)]
        v=[c[t]-a[t] for t in range(3)]
        cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        scale=math.sqrt(sum(e*e for e in cross))
        area+=0.5*scale
        dot=sum(cross[t]*normals[i][t] for t in range(3))
        if dot>1e-10:pos+=1
        elif dot< -1e-10:neg+=1
        else:zero+=1
    return {"triangles":len(indices)//3,"area":area,
            "normal_positive":pos,"normal_negative":neg,"degenerate":zero}

def main(source,converted):
    origin=stats(*glb_payload(source))
    target=stats(*iqm_payload(converted))
    ratio=target["area"]/origin["area"] if origin["area"] else 0
    positive_origin=origin["normal_positive"]/origin["triangles"]
    positive_target=target["normal_positive"]/target["triangles"]
    checks={
       "triangles_preserved":target["triangles"]==origin["triangles"],
       "normal_facing_preserved":abs(positive_origin-positive_target)<=0.01,
       "area_preserved_within_1pct":abs(ratio-1)<=0.01,
       "no_degenerate_faces":target["degenerate"]==origin["degenerate"]==0
    }
    print(json.dumps({"source":origin,"converted":target,"area_ratio":ratio,
                      "checks":checks,"note":"Procedural 20K fixture, NOT MP40/visual validation"},indent=2))
    return 0 if all(checks.values()) else 1

if __name__=="__main__":
    try:sys.exit(main(Path(sys.argv[1]),Path(sys.argv[2])))
    except (ValueError,OSError,IndexError,struct.error,KeyError) as exc:
        print(f"GEOMETRY_PARITY_ERROR: {exc}",file=sys.stderr);sys.exit(2)
