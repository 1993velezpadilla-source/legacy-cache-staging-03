# Candyland Four-Agent Coordination

## Agent A — Build Engineer
Owns map integration, Blender world build, exports, engine compile, Android runtime.

## Agent B — 3D Asset Engineer
Owns detection, segmentation, image-to-3D, mesh cleanup, asset QA, GLB handoff.

## Agent C — Research & Data Scout
Finds verified tools, assets, packs, licenses, models, benchmarks, and fallbacks.

## Agent D — Coding Support & QA
Fixes code/workflows, writes tests, reproduces failures, validates outputs, and unblocks A/B/C.

## Handoff flow
C -> B: verified model/tool/asset candidates.
C -> A: verified map/environment/audio/texture resources.
B -> D: failing reconstruction/cleanup/import scripts.
D -> B: repaired/tested asset pipeline.
B -> A: approved GLBs + asset manifest + QA renders.
A -> D: failing build/export/engine/Android logs.
D -> A: repaired/tested build pipeline.
A -> all: final runtime/visual QA results.

## Automation rule
No agent should wait on another if a safe fallback exists. Use the fallback, record the limitation, and continue producing artifacts.
