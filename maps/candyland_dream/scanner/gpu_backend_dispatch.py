#!/usr/bin/env python3
"""GPU backend dispatcher contract for CandyAssetScanner.

This file intentionally does not hide missing GPU/model dependencies.
It consumes quality_queue.json and emits commands/manifests for the selected
backend. TRELLIS is the default quality backend; TripoSR is the fast backend.

The runner should install the chosen official project according to its own
README and model license. Generated GLBs must preserve the scanner item id.
"""
import argparse,json,shlex
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("scanner_dir"); ap.add_argument("--backend",choices=["trellis","triposr","hunyuan"],default="trellis")
args=ap.parse_args()
root=Path(args.scanner_dir); q=json.loads((root/"quality_queue.json").read_text())
out=root/"gpu_jobs"; out.mkdir(exist_ok=True)
jobs=[]
for item in q:
    crop=root/item["crop"]
    target=out/f'{item["id"]}.glb'
    jobs.append({"id":item["id"],"backend":args.backend,"input":str(crop),"output":str(target),"label":item["label"]})
(out/f"{args.backend}_jobs.json").write_text(json.dumps(jobs,indent=2))
print(json.dumps({"status":"GPU_JOB_MANIFEST_READY","backend":args.backend,"jobs":len(jobs)},indent=2))
