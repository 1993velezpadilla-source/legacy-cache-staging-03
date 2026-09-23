#!/usr/bin/env python3
import json, sys
from pathlib import Path
import trimesh

out=Path(sys.argv[1])
files=[out/"candyland_dream_v03.glb",out/"candy_props_v03.glb"]
result={"ok":True,"files":[]}
for p in files:
    if not p.is_file() or p.stat().st_size<1024:
        raise SystemExit(f"missing/too-small GLB: {p}")
    s=trimesh.load(p,force="scene")
    meshes=[g for g in s.geometry.values()]
    tris=sum(len(g.faces) for g in meshes if hasattr(g,"faces"))
    if not meshes or tris<=0:
        raise SystemExit(f"no mesh triangles: {p}")
    result["files"].append({"name":p.name,"bytes":p.stat().st_size,"meshes":len(meshes),"triangles":tris,"bounds":s.bounds.tolist()})
(out/"glb_validation.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
