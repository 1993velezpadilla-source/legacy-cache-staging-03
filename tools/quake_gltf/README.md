# Vril / NZ:P — GLB & high-fidelity model intake (2026-10-14)

Status: **PREFLIGHT TOOL TESTED LOCALLY**; **NO GLB IMPORTER OR APK BUILT**. Development branch is not production. The first job is to stop damaging sources by blindly converting them to legacy Quake MDL.

## Verified upstream components
- **FTEQW iqmtool**: accepts .gltf and .glb and converts to .iqm or .mdl. Reference: https://github.com/fte-team/fteqw (see ftetools_readme.txt, IQM TOOL). The .iqm path preserves skeletal animation and is preferable to baking frames into MDL. That does **not** mean current Android Vril loads IQM.
- **FTEQW skeletal model pipeline**: IQM preferred, with PSK and MD5 options. Reference: https://github.com/fte-team/fteqw (specs/skeletal.txt). Consider selectively porting model loader/skinning/rendering, not replacing the whole NZ:P engine untested.
- **cgltf**: standalone C99 GLB/glTF parser. https://github.com/jkuhlmann/cgltf — parsing alone does not implement rendering, material shaders, skeletal animation, glTF extensions or GL state management.
- **NZ:P Blender MDL exporter**: https://docs.nzp.gay/mapping/model-exporting has viewmodel bounding-box controls that reduce vertex swimming in legacy pipeline.
- **Khronos glTF Validator**: https://github.com/KhronosGroup/glTF-Validator to catch bad buffers/accessors, skin errors, assets and more.
- **Existing owner's XZSM static-mesh Vril render bridge**: https://github.com/1993velezpadilla-source/config-old-3/blob/main/scripts/patch_vril_sanctum_staticmesh.py proves a separate high-detail textured model draw path was designed for Vril SDL. **It does not support animated MP40s** as written.

## Two parallel experimental tracks
**Track A — fastest diagnostic**: Read *source* GLB → run Khronos validator → run `python3 tools/quake_gltf/preflight.py path/to/mp40.glb` → export using FTEQW `iqmtool` to IQM; inspect without re-topology, quantization, reorientation or texture loss. Test one original + optional exported IQM rendering in a compatible reference engine. Measure triangle counts, skeleton, animations and UV/material parity.

**Track B — targeted Android runtime support**: Keep NZ:P's QuakeC gameplay / MDL fallback. Add GLB/IQM-aware model type, renderer and asset lookup to Vril's SDL GLES path, based on existing gl_model.c and gl_rmain.c model dispatch. Implement local/world transforms, winding/determinant and correct cull state, index buffers, base color/normal maps as supported, bones+weights, interpolation and animation names/mapping (including weapon, magazine and hands). Preserve draw/world/collision authority. Port one format **only after** identifying the easiest proven path; do not mix ad-hoc MDL frame modifications into the new importer.

## Mandatory first MP40 gauntlet
1. GLB structurally valid, all expected meshes present, 3,593-triangle claim verified against source (no hard-coded expectation).
2. Inspect source/converted normals, clockwise-vs-CCW winding, mirror transforms, mesh primitive/material split, UV mapping, indexed triangles, double-sided alpha and missing textures.
3. Verify magazine, hands, sights and gun attachment bones and bind matrices. Never flatten or rebuild them unless necessary.
4. Confirm GLB→IQM path retains triangle count, UVs, normals, names and animation data with visual comparison.
5. Compare **source GLB / reference render / Vril Android screenshot** at same orientation, pose, FOV and light. Do not treat green compilation as visual success.
6. Verify Android GLES CPU/GPU memory and FPS on real Pixel Fold device; no claim of 1:1 PBR until the renderer/shaders actually pass.

## Safe constraints
No polygon decimation, no automatic texture resolution reduction, no 46-frame bake as the preferred path. Multi-material and PBR fidelity are **renderer features**, not properties a file converter can guarantee. Do not import proprietary commercial game assets into public repos without licensing rights. The preflight script is read-only and reports metadata; it cannot prove normals, topology, occlusion or rendering correctness.

Run unit tests with `cd tools/quake_gltf && python3 -m unittest -v` and inventory with `python3 tools/quake_gltf/preflight.py mp40.glb --triangle-budget 16384`. Optional triangle budget is just a warning and may not reflect the active engine build.
