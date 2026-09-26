#!/usr/bin/env python3
"""Stage original WaW Mod Tools source assets for the Nacht GOLDEN benchmark.

Consumes a local checkout of the World at War Mod Tools and copies selected
original-source assets into a benchmark staging directory, recording SHA-256
for reproducibility.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import shutil
from pathlib import Path

PATTERNS = [
    "raw/maps/nazi_zombie_prototype.gsc",
    "raw/maps/nazi_zombie_prototype_fx.gsc",
    "raw/maps/createart/nazi_zombie_prototype_art.gsc",
    "raw/maps/createfx/nazi_zombie_prototype_fx.gsc",
    "raw/clientscripts/createfx/nazi_zombie_prototype_fx.csc",
    "raw/soundaliases/nazi_zombie_prototype.csv",
    "zone_source/nazi_zombie_prototype.csv",

    "map_source/_prefabs/zombiemode/*.map",
    "raw/character/*zombie*.gsc",
    "raw/character/*zombie*.csv",
    "raw/aitype/*zombie*.gsc",
    "raw/aitype/*zombie*.csv",
    "raw/animscripts/**/*zombie*.gsc",
    "raw/animtrees/*zombie*",
    "detail_maps/**/*zombie*",

    "model_export/viewmodels/**/*zombie*",

    "model_export/american/weapons/SMGs/thompson/**/*",
    "raw/sound/SFX/weapon/SMG/Thompson/**/*",
    "raw/sound/SFX/weapon/SMG/mp40/**/*",
    "raw/sound/SFX/weapon/pistols/colt1911/**/*",
    "raw/sound/SFX/weapon/ray_gun/**/*",

    "raw/materials/*thompson*",
    "raw/materials/*mp40*",
    "raw/materials/*colt*",
    "raw/materials/*ray_gun*",
    "raw/material_properties/*thompson*",
    "raw/material_properties/*mp40*",
    "raw/material_properties/*colt*",
    "raw/material_properties/*ray_gun*",
    "raw/phys_collmaps/*thompson*",
    "raw/phys_collmaps/*mp40*",
    "raw/phys_collmaps/*colt*",
    "raw/phys_collmaps/*ray_gun*",
]

EXCLUDES = ["*.exe", "*.dll"]


def selected(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    if any(fnmatch.fnmatch(rel, pat) for pat in EXCLUDES):
        return False
    return any(fnmatch.fnmatch(rel, pat) for pat in PATTERNS)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("modtools_root", type=Path)
    ap.add_argument("output_root", type=Path)
    args = ap.parse_args()

    src = args.modtools_root.resolve()
    dst = args.output_root.resolve()
    if not src.is_dir():
        raise SystemExit(f"missing Mod Tools root: {src}")

    dst.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema": 1,
        "source_root": str(src),
        "files": [],
    }

    for path in sorted(p for p in src.rglob("*") if p.is_file()):
        rel = path.relative_to(src).as_posix()
        if not selected(rel):
            continue

        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out)

        manifest["files"].append({
            "path": rel,
            "size": path.stat().st_size,
            "sha256": file_sha256(path),
        })

    manifest["file_count"] = len(manifest["files"])
    manifest["total_bytes"] = sum(x["size"] for x in manifest["files"])

    manifest_path = dst / "nacht_modtools_stage_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"staged {manifest['file_count']} files")
    print(f"manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
