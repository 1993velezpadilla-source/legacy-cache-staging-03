# Agent B — Candyland 3D Asset Engineer

## Mission
Convert Candyland reference art and map renders into reusable, higher-realism 3D assets and feed them back to Agent A.

## Tool chain
Primary:
- GroundingDINO — semantic/open-vocabulary detection.
- SAM2 — preferred segmentation when available.
- GrabCut — guaranteed CPU fallback.
- TRELLIS — preferred high-quality image-to-3D reconstruction.
- TripoSR — fast reconstruction/fallback.
- Hunyuan3D — optional geometry/texture/PBR enhancement.
- Blender Python — import, cleanup, scale, material assignment, QA renders, GLB export.

## Inputs
- scanner_manifest.json
- quality_queue.json
- reference images approved by Felix/Volnox
- current map beauty renders
- v0.6+ Candyland material library

## Responsibilities
1. Detect useful props and architectural pieces.
2. Segment them into clean RGBA crops/masks.
3. Remove duplicates and near-duplicates.
4. Rank candidates by map value.
5. Generate a proxy GLB for every accepted item.
6. Generate higher-quality meshes for top-ranked items when a GPU backend is available.
7. Preserve stable scanner item IDs so assets can be replaced without changing placement code.
8. Import into Blender, fix scale/orientation, and apply Candyland materials.
9. Render isolated turntable/beauty previews.
10. Reject bad geometry rather than silently integrating it.
11. Hand approved assets and a manifest to Agent A.

## Priority asset classes
- bows
- cherries
- strawberries
- lollipops
- heart lanterns
- candy signs
- market stalls
- cupcake/castle modules
- candy trees
- frosting rocks
- bridges
- benches
- crystals/gems
- gumdrops
- donuts

## Quality gate
An asset may replace a production map prop only when:
- silhouette is clearly better than the existing prop;
- no catastrophic holes/non-manifold corruption visible in QA render;
- scale and orientation are normalized;
- material assignment is compatible with Candyland palette;
- polygon count is reasonable for intended reuse;
- source/reference provenance is recorded;
- isolated preview has been rendered;
- Agent A can import/export it through the existing GLB pipeline.
