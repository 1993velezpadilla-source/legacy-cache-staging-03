# Candyland Dream v0.3 Execution Report

Date: 2026-09-22/23
Workflow run: 35813662479
Result: SUCCESS

## Five-agent execution

1. Agent 1 — Blender scene + preview execution: SUCCESS
   - Generated editable BLEND.
   - Exported full Candyland GLB.
   - Exported procedural candy-prop GLB.
   - Rendered isometric, spawn, and castle preview images.

2. Agent 2 — Procedural 3D asset generation: SUCCESS
   - Verified 13 generated prop objects.
   - Verified the generated preview set and asset GLB.

3. Agent 3 — GLB export/import validation: SUCCESS
   - Re-imported exported GLB files using an independent glTF-capable mesh validator.
   - Confirmed real mesh geometry exists.

4. Agent 4 — NZ:P/Vril map compiler compatibility: SUCCESS
   - Exported Candyland as an NZ:P-compatible MAP harness.
   - Compiled candyland_harness.bsp.
   - Compiled candyland_harness.nsz.

5. Agent 5 — Vril Android emulator first-frame smoke: SUCCESS
   - Built Xziel/Vril Android debug APK with Candyland BSP/NSZ bundled.
   - Cold-launched com.xziel.nzp on an Android 35 Pixel 6 emulator profile.
   - Runtime process remained alive.
   - Verified STAGE=FIRST_FRAME_OK.
   - Verified runtime map files were installed.
   - Captured two 2400x1080 frames.
   - Frame A luminance stddev: 85.37.
   - Frame B luminance stddev: 85.30.
   - Frame delta mean: 0.275.

## Blender output report
- Version: 0.3.0
- Visual meshes: 48
- Visual triangles: 6,248
- Procedural asset objects: 13
- Route nodes: 8
- Main path width: 5.0 m
- Player clearance target: 1.2 m

## Android evidence
- PID: 2294
- Runtime stage: FIRST_FRAME_OK
- candyland_harness.bsp installed: 428,904 bytes
- candyland_harness.nsz installed: 117 bytes
- APK artifact produced.
- Emulator screenshots produced.

## Runtime scope
The engine smoke harness validates loading, BSP/NSZ compatibility, Android packaging, launch, and rendering. It does not yet claim that Vril renders the exact Blender GLB visual scene; that requires a dedicated Vril static-mesh/renderer integration pass.
