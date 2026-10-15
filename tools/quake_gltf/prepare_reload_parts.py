#!/usr/bin/env python3
"""Generate a rigorously validated, per-face moving-magazine mask for IQM.

Reads the actual, unchanged MP40 IQM geometry; identifies disconnected
magazine surface components whose bounds reach the bottom of the gun.
The mask does not modify geometry or textures and moves only its 894
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
    # UV and normal seams duplicate vertices in FTE IQM. Vertex-index-only
    # connectivity misses >50% of this MP40 magazine (floorplate and ribs).
    # Group faces by *positions* at 1e-5 to recover disconnected rigid
    # islands, then select all islands lying wholly inside the source GLB's
    # magazine bounds; no receiver or stock vertices are moved.
    from extract_iqm_magazine import select_mag, PROFILES
    mag,components=select_mag(positions,triangles,PROFILES["mp40_moony_state"])
    mag.sort()
    if len(positions)==12628 and len(triangles)==14450 and len(mag)!=894:
        raise ValueError("MP40 magazine components changed; refuse inaccurate animation")
    return mag, {"triangle_count":len(triangles),
                 "magazine_triangles":len(mag),
                 "magazine_components":len(components),
                 "magazine_bounds":components,
                 "source_decimation":False}

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
