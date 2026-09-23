# Candyland Dream Status

## Phase
V0.3 EXECUTED_AND_RUNTIME_SMOKE_VERIFIED

## Verified execution
- [x] Blender scene generation.
- [x] Blender preview renders.
- [x] Procedural 3D candy asset generation.
- [x] GLB export.
- [x] GLB re-import/mesh validation.
- [x] NZ:P BSP + NSZ compilation with the official NZ:P toolchain.
- [x] Vril Android APK build with Candyland map bundled.
- [x] Android emulator cold launch.
- [x] Runtime first-frame check: FIRST_FRAME_OK.
- [x] Runtime screenshots captured and checked as non-flat frames.

## Build facts
- Version: 0.3.0
- Visual meshes: 48
- Visual triangles: 6,248
- Procedural asset objects: 13
- Route nodes: 8
- Main path width: 5.0 m
- Player clearance target: 1.2 m
- Android runtime map: candyland_harness.bsp + candyland_harness.nsz
- Verified Android process PID in CI: 2294
- Verified runtime stage: FIRST_FRAME_OK

## Evidence
GitHub Actions workflow: Candyland Dream Five-Agent Runtime Pipeline
Successful run: 35813662479
Head commit: 06fe8be3dbb9442766647524e503b1d6282d5bae

Artifacts produced by the successful run:
- candyland-agent1-blender
- candyland-agent2-assets
- candyland-agent3-glb
- candyland-agent4-engine-harness
- candyland-agent5-android-runtime

## Important visual-runtime distinction
The Vril/NZ:P Android smoke harness proves that the compiled Candyland map package loads and reaches a rendered first frame. The current Vril harness uses engine-native BSP presentation for runtime compatibility. The richer candy-colored Blender GLB scene is generated and validated separately; bringing that exact visual dressing into Vril is a later renderer/static-mesh integration pass, not part of this smoke-test claim.
