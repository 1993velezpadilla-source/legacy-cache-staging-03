# CandyAssetScanner v0.7

Purpose: turn approved Candyland reference images into a reproducible asset queue for the real map.

## Backends

- Detection: GroundingDINO (Apache-2.0) when available.
- Segmentation: SAM 2 (Apache-2.0 checkpoints/code) when available.
- Fast image-to-3D: TripoSR (MIT) when a compatible GPU/runtime is available.
- High-quality image-to-3D: TRELLIS (MIT majority; audit submodule licenses before redistribution).
- Texture/PBR enhancement: Hunyuan3D-2 family as an optional external backend; exact model/license must be recorded.
- CPU-safe fallback: OpenCV GrabCut plus Blender procedural class templates. The fallback is intentionally deterministic so CI can still create real Blender/GLB assets when hosted runners have no GPU.

## Pipeline contract

1. reference image -> detector
2. boxes + labels -> segmenter
3. masks/crops -> rank/dedupe
4. top assets -> AI 3D backend when available
5. unavailable/failed AI 3D -> procedural Blender fallback
6. every mesh -> normalize scale/orientation/material family
7. render turntable/contact sheet
8. approve by manifest
9. integrate approved assets into Candyland v0.7
10. GLB + engine + Android QA

## Production classes

Highest priority:
- satin bow
- cherry
- strawberry
- heart lantern
- heart crystal
- lollipop tree
- candy market stall
- cupcake/castle tower
- candy signpost
- frosting rock/cliff
- wafer bridge decoration
- candy bench

## Provenance

Each job records:
- source reference
- detector/backend
- detection confidence
- segmentation backend
- 3D backend
- source/model license
- SHA-256 for generated/imported files
- fallback reason if AI generation was unavailable

Generated assets are drafts until the Blender QA gate passes.
