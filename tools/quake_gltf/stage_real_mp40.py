#!/usr/bin/env python3
"""Stage a REAL CC BY MP40 IQM + albedo for the Android NZ:P preview APK.

Input MP40 is the complete public 4.4MB GLB by Moony_State (Sketchfab/Zenodo).
No dummy model, no replacement with a human, no decimation/downsampling.
Fail closed if material->texture mapping cannot be established unambiguously.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path
from extract_basecolor import extract, _safe_name
from inspect_iqm import parse_iqm, compare
from preflight import parse_glb
from prepare_reload_parts import generate as generate_reload_parts

SOURCE_MD5="733d3ce5428a6451ec5231fa18e84058"
MODEL_ID="7ec7e1f9656e4319b8edae0d785699ad"
ATTRIBUTION="""MP 40 - WW2 Submachine Gun
Author: Moony_State (Sketchfab)
Source: https://sketchfab.com/3d-models/mp-40-ww2-submachine-gun-7ec7e1f9656e4319b8edae0d785699ad
Zenodo file: https://zenodo.org/records/10379721
License: Creative Commons Attribution 4.0 (CC BY 4.0)
https://creativecommons.org/licenses/by/4.0/
Converted from GLB to IQM with FTEQW iqmtool, without intentional polygon
decimation or texture recompression; experimental Vril rendering conversion.
No affiliation with the original author. Original model is not BO3 game art.
"""
def main(glb,iqm,overlay):
    if hashlib.md5(glb.read_bytes()).hexdigest()!=SOURCE_MD5:
        raise ValueError("Source MP40 file checksum mismatch; refusing unverified bytes")
    p=compare(glb,iqm)
    if p["structural_errors"]:
        raise ValueError("Geometry mismatch: "+str(p["structural_errors"]))
    source=p["source"]
    if source["triangles"]<10000:
        raise ValueError("Downloaded MP40 has unexpectedly low triangle count")
    target=Path(overlay)/"models/weapons/mp40"
    target.mkdir(parents=True,exist_ok=True)
    doc,_=parse_glb(glb)
    records=extract(glb,target)
    if not records:raise ValueError("MP40 has no base-color texture; don't release untextured preview")
    materials=set(_safe_name(x["material"]) for x in records)
    iqm_meshes=parse_iqm(iqm)["meshes"]
    if not iqm_meshes:raise ValueError("IQM lacks meshes")
    for mesh in iqm_meshes:
        name=_safe_name(mesh["material"])
        if not name:raise ValueError("IQM empty material string")
        candidates=[p for p in target.iterdir() if p.stem==name and p.suffix in (".png",".jpg")]
        if not candidates:
            if len(records)!=1:raise ValueError("Ambiguous multi-material mapping: "+name)
            src=Path(records[0]["texture_path"])
            dst=target/(name+src.suffix)
            if dst!=src:shutil.copyfile(src,dst)
        else:dst=candidates[0]
        print("MP40_IQM_MATERIAL_TEXTURE",mesh["material"],dst.name,dst.stat().st_size)
    out=target/"v_mp40.iqm"
    shutil.copyfile(iqm,out)
    segmentation=generate_reload_parts(iqm,target/"v_mp40.iqmparts")
    if segmentation["magazine_triangles"]!=348:
        raise ValueError("MP40 magazine must remain a source-derived 348-triangle component")
    licensepath=Path(overlay)/"licenses/MP40-MoonyState-CC-BY-4.0.txt"
    licensepath.parent.mkdir(parents=True,exist_ok=True)
    licensepath.write_text(ATTRIBUTION)
    print(json.dumps({"MP40_GLB_SOURCE_TRIANGLES":source["triangles"],
        "MP40_IQM_TRIANGLES":p["converted"]["triangles"],
        "MP40_IQM_MESHES":len(iqm_meshes),"source_images":len(records),
        "iqm":str(out),"magazine_mask":segmentation,
        "license":str(licensepath)},indent=2))
if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: stage_real_mp40.py <source.glb> <converted.iqm> <overlay-root>")
    main(*map(Path,sys.argv[1:]))
