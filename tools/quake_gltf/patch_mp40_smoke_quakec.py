#!/usr/bin/env python3
"""TEST ONLY: spawn carrying NZ:P's actual MP40 for an IQM sidecar screenshot.

This is applied to a throwaway QuakeC clone inside the experimental APK CI.
Never change the production QuakeC rules or gameplay start weapon.
"""
import sys
from pathlib import Path

def patch(root: Path):
    path=root/"source/server/player/player_core.qc"
    original=path.read_text()
    anchor="Weapon_AssignWeapon(0, spawn_point.weapon, spawn_point.currentmag, spawn_point.currentammo, 0);"
    replacement="Weapon_AssignWeapon(0, W_MP40, 32, 192, 0); /* IQM smoke build only */"
    if replacement in original:
        print("MP40_SMOKE_START_WEAPON_ALREADY_PATCHED")
        return
    if original.count(anchor)!=1:
        raise RuntimeError(f"Expected one start-weapon assignment in {path}, got {original.count(anchor)}")
    path.write_text(original.replace(anchor,replacement,1))
    print("MP40_SMOKE_START_WEAPON_PATCHED")

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: patch_mp40_smoke_quakec.py <quakec-source-root>")
    patch(Path(sys.argv[1]))
