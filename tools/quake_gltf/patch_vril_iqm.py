#!/usr/bin/env python3
"""Add IQM opt-in sidecar drawing to Vril SDL compatibility renderer.

Usage:
  python3 tools/quake_gltf/patch_vril_iqm.py /path/to/vril-engine

Safe to re-run. Default cvar=0 keeps every original MDL and QuakeC behavior.
This is stage-1 BIND-POSE GEOMETRY ONLY, NOT skeletal animation.
"""
import shutil
import sys
from pathlib import Path

def replace_once(data: str, original: str, new: str, label: str):
    if new in data:
        return data
    count = data.count(original)
    if count != 1:
        raise RuntimeError(f"{label}: expected one source anchor, found {count}")
    return data.replace(original, new, 1)

def patch(root: Path):
    root = root.resolve()
    gl_dir = root / "source" / "platform" / "sdl" / "gl"
    if not gl_dir.is_dir():
        raise RuntimeError(f"Vril SDL GL directory missing: {gl_dir}")
    source = Path(__file__).with_name("gl_xziel_iqm_viewmodel.c")
    if not source.is_file():
        raise RuntimeError(f"Missing bundled IQM implementation {source}")
    # Verify all edits before writing any target file.
    model = gl_dir / "gl_model.c"
    main = gl_dir / "gl_rmain.c"
    model_body = model.read_text()
    main_body = main.read_text()

    model_updated = replace_once(
        model_body,
        "Cvar_RegisterVariable (&gl_subdivide_size);\n",
        "Cvar_RegisterVariable (&gl_subdivide_size);\n\tXziel_IQM_Init();\n",
        "Mod_Init"
    )
    model_updated = replace_once(
        model_updated,
        'void Mod_LoadAliasModel (model_t *mod, void *buffer);\n',
        'void Mod_LoadAliasModel (model_t *mod, void *buffer);\nvoid Xziel_IQM_Init(void);\n',
        "IQM init declaration"
    )
    main_updated = replace_once(
        main_body,
        '#include "../../../nzportable_def.h"\n',
        '#include "../../../nzportable_def.h"\n\n'
        'qboolean Xziel_IQM_DrawViewModel(entity_t *e);\n',
        "Renderer declaration"
    )

    names = ("void R_DrawView2Model (void)", "void R_DrawViewModel (void)")
    for i, name in enumerate(names):
        begin = main_updated.find(name)
        if begin < 0:
            raise RuntimeError(f"Missing {name}")
        end = main_updated.find(names[1], begin+len(name)) if i == 0 else main_updated.find("void R_PolyBlend (void)", begin)
        if end < 0:
            raise RuntimeError(f"Could not find end of {name}")
        section = main_updated[begin:end]
        marker = "\tR_DrawAliasModel (currententity);\n"
        replacement = "\tif (!Xziel_IQM_DrawViewModel(currententity))\n\t\tR_DrawAliasModel (currententity);\n"
        section = replace_once(section, marker, replacement, name)
        main_updated = main_updated[:begin] + section + main_updated[end:]

    dest = gl_dir / source.name
    # Exactly one C file, no alteration of QuakeC, BSP or original MDL assets.
    model.write_text(model_updated)
    main.write_text(main_updated)
    shutil.copy2(source, dest)
    print("XZIEL_IQM_PATCHED: optional IQM bind-pose model sidecars; MDL fallback")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_vril_iqm.py <vril-engine-root>")
    patch(Path(sys.argv[1]))
