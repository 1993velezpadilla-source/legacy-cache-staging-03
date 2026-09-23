#!/usr/bin/env python3
"""Export a lightweight Candyland Dream runtime manifest.

This is an engine-neutral companion to the Blender blockout.
It reads measurements.json and writes a deterministic map manifest.
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEASUREMENTS = ROOT / "measurements.json"
OUT = ROOT / "previews" / "candyland_runtime_manifest.json"

data = json.loads(MEASUREMENTS.read_text(encoding="utf-8"))
identity = json.dumps(data, sort_keys=True, separators=(",", ":"))
manifest = {
    "map": data["name"],
    "version": data["version"],
    "status": data["status"],
    "footprint_m": data["playable_area"],
    "landmarks": {
        key: data[key]
        for key in ("spawn", "candy_plaza", "lollipop_forest", "chocolate_river", "cupcake_castle")
    },
    "gameplay_route": [
        "spawn",
        "candy_plaza",
        "lollipop_forest",
        "chocolate_river",
        "cupcake_castle"
    ],
    "runtime_layers": ["visual", "walkable", "collision", "navigation", "gameplay_triggers"],
    "source_measurements_sha256": hashlib.sha256(identity.encode("utf-8")).hexdigest(),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"WROTE {OUT}")
