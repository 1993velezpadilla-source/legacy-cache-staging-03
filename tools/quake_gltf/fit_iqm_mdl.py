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
import re
import statistics
from pathlib import Path

def mdl_bbox(path, hands_only=None):
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
    pos+=12*verts
    tris_offset=pos
    stock_triangles={tuple(struct.unpack_from("<4I",b,tris_offset+16*i))
                     for i in range(tris)}
    selected_verts=None
    if hands_only is not None:
        # The authoring Blender rig and 46 stock MDL frames are preserved.
        # But the full source frame bounding-box INCLUDES the animated hands.
        # Its lateral midpoint is -4.41 Quake units; the actual gun centroid
        # is -11.47, a 7-unit separation already visible on the Pixel Fold.
        # Derive the modern-gun fit from the STOCK GUN-ONLY mesh instead.
        h=Path(hands_only).read_bytes()
        # Byte 64..67 is numtris, intentionally DIFFERENT in hands-only MDL.
        # Require the original stock header and frame count everywhere else.
        if len(h)<84 or h[:64]!=b[:64] or h[68:84]!=b[68:84]:
            raise ValueError("hand separation is not from same stock MDL")
        hand_tris=struct.unpack_from("<I",h,64)[0]
        if not 120<=hand_tris<=550 or struct.unpack_from("<I",h,68)[0]!=frames:
            raise ValueError("hands-only mask has unexpected frame count/faces")
        hand_faces_start=tris_offset
        hand_faces={tuple(struct.unpack_from("<4I",h,hand_faces_start+16*i))
                    for i in range(hand_tris)}
        if not hand_faces.issubset(stock_triangles):
            raise ValueError("hands-only contains non-original gun faces")
        gun_faces=stock_triangles-hand_faces
        if len(gun_faces)<200:
            raise ValueError("not enough original gun triangles after segmentation")
        hand_vert_ids={vi for face in hand_faces for vi in face[1:]}
        selected_verts={vi for face in gun_faces for vi in face[1:]}-hand_vert_ids
        if not 300<=len(selected_verts)<=1800:
            raise ValueError("invalid gun-only independent vertex count")
    pos+=16*tris
    if pos+28+verts*4>len(b):raise ValueError("missing first MDL frame")
    frametype=struct.unpack_from("<I",b,pos)[0];pos+=4
    if frametype!=0:raise ValueError("grouped first frame unsupported")
    pos+=24
    coords=[tuple(origin[i]+scale[i]*b[pos+4*k+i] for i in range(3))
            for k in (sorted(selected_verts) if selected_verts is not None else range(verts))]
    return [min(v[i] for v in coords) for i in range(3)], [max(v[i] for v in coords) for i in range(3)]

def iqm_positions(path):
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
            return coords
    raise ValueError("missing float POSITION")

def weapon_source_frames(path, weapon):
    """Authoritative offsets/frame boundaries from NZ:P QuakeC, not COD guesses."""
    src=path.read_text()
    get_ads=re.search(r'vector GetWeaponADSOfs\s*\(float wep\)\s*=.*?(?=float\(float wep, float frametype)',src,re.S)
    get_frames=re.search(r'float\(float wep, float frametype.*?GetFrame\s*=.*?(?=string\(float wep|float\(float wep)',src,re.S)
    if not get_ads or not get_frames: raise ValueError("QuakeC ADS/frame functions absent")
    def block(section, ending="break"):
        # QuakeC ADS directly RETURNS; GetFrame uses a nested switch and BREAK.
        matches=list(re.finditer(r'case\s+W_[A-Z0-9_]+\s*:',section))
        target=next((i for i,m in enumerate(matches) if m.group().split()[1][:-1]==weapon),None)
        if target is None: raise ValueError("Missing weapon "+weapon)
        tail=section[matches[target].start():]
        if ending=="return":
            m=re.search(r'return\s*\[[^;]*\]\s*;',tail)
            if not m:raise ValueError("No direct ADS return for "+weapon)
            return tail[:m.end()]
        end=tail.find("break;")
        if end<0: raise ValueError("Unterminated frame block "+weapon)
        return tail[:end]
    ads=block(get_ads.group(),ending="return")
    numbers=re.search(r'return\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]',ads)
    if not numbers:raise ValueError("ADS offsets not numeric for "+weapon)
    # QuakeC: offset [0] = raw barrel lateral, [1] = vertical, [2] = forward.
    raw=tuple(float(x) for x in numbers.groups())
    ads_y=-raw[0]/1000.0
    ads_z=raw[1]/1000.0
    anim=block(get_frames.group())
    def frame(label):
        r=re.search(r'case\s+'+label+r'\s*:\s*return\s+(\d+)\s*;',anim)
        if not r:raise ValueError("Missing "+label+" for "+weapon)
        return int(r.group(1))
    first,last=frame("RELOAD_START"),frame("RELOAD_END")
    if not (0<ads_y<100 and -100<ads_z<100 and 1<=first<last<=255):
        raise ValueError("Implausible QuakeC weapon parameters")
    return ads_y,ads_z,first,last

def sight_line(coords):
    """Rear sight ROI: top of first receiver segment, excluding rear stock/front sight."""
    xmin=min(v[0] for v in coords)
    xmax=max(v[0] for v in coords)
    span=xmax-xmin
    region=[v for v in coords if xmin+0.28*span<=v[0]<=xmin+0.45*span]
    if len(region)<50:raise ValueError("Insufficient geometry near rear receiver/sight")
    zs=sorted(v[2] for v in region)
    zcut=zs[int(0.97*(len(zs)-1))]
    high=[v for v in region if v[2]>=zcut]
    if len(high)<5:raise ValueError("Cannot infer rear sight from model")
    return statistics.median(v[1] for v in high), statistics.median(v[2] for v in high)


def front_sight(coords):
    """High-Z geometry in last 10% of barrel: actual front sight model landmark."""
    lo=min(v[0] for v in coords)
    hi=max(v[0] for v in coords)
    region=[v for v in coords if v[0] >= lo+0.90*(hi-lo)]
    if len(region)<10:raise ValueError("Not enough front muzzle/sight geometry")
    zs=sorted(v[2] for v in region)
    floor=zs[int(0.98*(len(zs)-1))]
    top=[v for v in region if v[2]>=floor]
    if len(top)<3:raise ValueError("No front iron sight reference")
    return [statistics.median(v[i] for v in top) for i in range(3)]


def write_alignment(mdl,iqm,dest,quakec=None,weapon=None,hands_only=None):
    amin,amax=mdl_bbox(mdl,hands_only)
    verts=iqm_positions(iqm)
    bmin=[min(v[i] for v in verts) for i in range(3)]
    bmax=[max(v[i] for v in verts) for i in range(3)]
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
    # One optional second line: authoritative ADS positional correction
    # and original MDL reload-frame interval. Runtime uses e->origin[1]
    # to blend only during ADS; idle transform remains unchanged.
    metadata=None
    if quakec is not None and weapon is not None:
        amplitude,vertical,first,last=weapon_source_frames(quakec,weapon)
        sight_y,sight_z=sight_line(verts)
        delta_y=-amplitude-(offsets[1]+factor*sight_y)
        delta_z=-vertical-(offsets[2]+factor*sight_z)
        if not all(math.isfinite(v) for v in (delta_y,delta_z)):
            raise ValueError("nonfinite ADS correction")
        metadata=[amplitude,delta_y,delta_z,first,last]+front_sight(verts)
    dest.parent.mkdir(parents=True,exist_ok=True)
    lines=[" ".join(f"{n:.9g}" for n in [factor]+offsets)]
    if metadata is not None:lines.append(" ".join(f"{n:.9g}" for n in metadata))
    dest.write_text("\n".join(lines)+"\n")
    report={"original_mdl_min":amin,"original_mdl_max":amax,
            "iqm_min":bmin,"iqm_max":bmax,
            "iqm_scale":factor,"xyz_offset":offsets,"ads_metadata":metadata,
            "sight_reference_from_geometry":sight_line(verts) if metadata else None,
            "front_sight_reference_from_geometry":front_sight(verts) if metadata else None,
            "source_vertex_decimation":False,
            "alignment_basis":"EXCLUSIVE_ORIGINAL_STOCK_GUN_NO_HANDS" if hands_only else "UNFILTERED_STOCK_MDL"}
    print(json.dumps(report,indent=2))
    return report

if __name__=="__main__":
    argv=sys.argv[1:]
    hands=None
    if "--hands-only" in argv:
        idx=argv.index("--hands-only")
        if idx+1>=len(argv):raise SystemExit("--hands-only requires MDL path")
        hands=Path(argv[idx+1])
        argv=argv[:idx]+argv[idx+2:]
    if len(argv) not in (3,5):
        raise SystemExit("usage: fit_iqm_mdl.py <viewmodel.mdl> <viewmodel.iqm> <viewmodel.iqmfit> [<QuakeC/weapon_stats.qc> <W_WEAPON>] [--hands-only <original-hands.mdl>]")
    args=list(map(Path,argv[:3]))
    if len(argv)==5:args.extend([Path(argv[3]),argv[4]])
    write_alignment(*args,hands_only=hands)
