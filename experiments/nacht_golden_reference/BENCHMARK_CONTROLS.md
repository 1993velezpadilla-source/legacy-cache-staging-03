# Nacht Benchmark Controls & Pass Matrix

## Current Xziel facts

- Android build currently defines `MAX_AI_COUNT=24`.
- Existing Xziel mobile patch raises the START ROUND selector ceiling to 255.
- Upstream Vril exposes server cheat commands including `god`, `noclip`, and `notarget`.

These capabilities should be surfaced through a benchmark-only developer menu rather than duplicated with new gameplay logic.

## Benchmark developer menu

Required controls:

- Enable benchmark cheats
- God mode toggle
- Noclip toggle
- Notarget toggle
- Start round: 1..255
- Restart current benchmark run
- Infinite ammo test toggle
- Zombie cap profile: 24 / 48 / 96
- Spawn pressure: 1x / 2x / 4x
- Freeze zombie spawning
- Kill all active zombies
- Telemetry overlay
- Screenshot marker / checkpoint id

All benchmark-only controls must be disabled/absent in normal shipping gameplay.

## Golden-reference pass matrix

| Layer | PASS condition | Failure points to engine |
|---|---|---|
| Geometry | expected world silhouette and local mesh shape remain stable | importer, coordinate conversion, vertex/index handling |
| UV | texture islands land on the expected surfaces | UV import, tangent/attribute indexing |
| Texture | near-field detail survives and mip transitions are stable | decode, compression, mip generation, filtering |
| Material | diffuse/specular/normal response is coherent | shader/material bridge |
| Lighting | reference mood is reproducible without crushed blacks or flat fullbright | lightmap/material/renderer path |
| Fog/sky | depth and exterior background behave consistently | fog state, sky path |
| FX | fire/smoke/sparks/water remain spatially correct | effect import/runtime |
| Viewmodel | arms/weapon retain geometry/material quality | weapon importer/render branch |
| Animation | idle/fire/reload/zombie movement play without corruption | animation conversion/runtime |
| Collision | player/zombies do not fall through or snag on visual-only defects | collision conversion |
| Navigation | zombies reach windows/player without systemic stalls | waypoint/nav runtime |
| Barricades | approach, attack, break and rebuild loop works repeatedly | gameplay/interaction |
| Rounds | round 1 through high-round override progresses without state corruption | game logic |
| Stress | target cap runs without crash/ANR/runaway memory | CPU/GPU/memory/nav scalability |

## Device stress gates

For every stress profile record:

- exact APK/build id
- device model
- Android version
- render resolution
- target FPS
- active-zombie peak
- average FPS
- 1% low FPS
- p95 and p99 frame time
- native/process memory
- temperature when available
- crash/ANR status
- screenshot at peak pressure

## Freeze rule

When a GOLDEN layer passes, store:
- input asset identity/hash;
- importer version;
- runtime format version;
- material/shader path;
- screenshot checkpoint;
- benchmark metrics.

Do not later "improve" GOLDEN. New rendering/asset ideas go into LAB and are compared A/B against the frozen control.
