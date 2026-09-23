#!/usr/bin/env python3
"""Optional GPU image-to-3D adapter for CandyAssetScanner.

Backends:
1. TRELLIS if importable and CUDA is available.
2. TripoSR if TRIPOSR_HOME points to a checkout and CUDA is available.
3. Skip cleanly; Blender procedural fallback remains authoritative.

This tool never overwrites an existing <class>.glb unless --overwrite is used.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

def load_queue(path: Path):
    return json.loads(path.read_text()).get("assets",[])

def cuda_ready():
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False

def run_trellis(assets, crop_root: Path, out: Path, overwrite=False):
    if not cuda_ready(): return [], "cuda_unavailable"
    try:
        from PIL import Image
        from trellis.pipelines import TrellisImageTo3DPipeline
        from trellis.utils import postprocessing_utils
    except Exception as e:
        return [], f"trellis_import_failed:{e!r}"
    pipeline=TrellisImageTo3DPipeline.from_pretrained(
        os.environ.get("TRELLIS_MODEL","microsoft/TRELLIS-image-large")
    )
    pipeline.cuda()
    made=[]
    for a in assets:
        cls=a["class"]; dst=out/f"{cls}.glb"
        if dst.exists() and not overwrite: continue
        crop=a.get("source_detection")
        if not crop: continue
        p=crop_root/crop
        if not p.exists(): continue
        image=Image.open(p).convert("RGB")
        outputs=pipeline.run(image,seed=1)
        glb=postprocessing_utils.to_glb(
            outputs["gaussian"][0],outputs["mesh"][0],
            simplify=.92,texture_size=1024
        )
        glb.export(str(dst)); made.append(str(dst))
    return made,"ok"

def run_triposr(assets,crop_root: Path,out: Path,overwrite=False):
    if not cuda_ready(): return [],"cuda_unavailable"
    home=os.environ.get("TRIPOSR_HOME")
    if not home: return [],"TRIPOSR_HOME_not_set"
    home=Path(home); runner=home/"run.py"
    if not runner.exists(): return [],f"missing:{runner}"
    made=[]
    for a in assets:
        cls=a["class"]; dst=out/f"{cls}.glb"
        if dst.exists() and not overwrite: continue
        crop=a.get("source_detection")
        if not crop: continue
        p=crop_root/crop
        if not p.exists(): continue
        with tempfile.TemporaryDirectory(prefix=f"triposr_{cls}_") as td:
            cmd=[sys.executable,str(runner),str(p),"--output-dir",td]
            subprocess.run(cmd,cwd=str(home),check=True)
            candidates=list(Path(td).rglob("*.obj"))+list(Path(td).rglob("*.glb"))
            if not candidates: continue
            src=candidates[0]
            if src.suffix.lower()==".glb":
                shutil.copy2(src,dst)
            else:
                try:
                    import trimesh
                    mesh=trimesh.load(src,force="mesh")
                    mesh.export(dst)
                except Exception:
                    continue
            made.append(str(dst))
    return made,"ok"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--queue",type=Path,default=Path("candyland/scanner/asset_queue.json"))
    ap.add_argument("--crop-root",type=Path,default=Path("candyland/scanner"))
    ap.add_argument("--out",type=Path,default=Path("candyland/scanner/ai3d"))
    ap.add_argument("--backend",choices=["auto","trellis","triposr"],default="auto")
    ap.add_argument("--overwrite",action="store_true")
    args=ap.parse_args(); args.out.mkdir(parents=True,exist_ok=True)
    assets=load_queue(args.queue)
    attempts=[]; made=[]
    order=[args.backend] if args.backend!="auto" else ["trellis","triposr"]
    for backend in order:
        try:
            if backend=="trellis": files,status=run_trellis(assets,args.crop_root,args.out,args.overwrite)
            else: files,status=run_triposr(assets,args.crop_root,args.out,args.overwrite)
        except Exception as e:
            files=[]; status=f"error:{e!r}"
        attempts.append({"backend":backend,"status":status,"files":files})
        made.extend(files)
        if files and args.backend=="auto": break
    report={
        "status":"AI3D_COMPLETE" if made else "AI3D_NOT_AVAILABLE_USING_PROCEDURAL_FALLBACK",
        "cuda_ready":cuda_ready(),
        "attempts":attempts,
        "generated":made,
    }
    (args.out/"ai3d_report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
