# CandyAssetScanner v0.7

Automated reference-image-to-3D-asset pipeline for Candyland Dream.

## Production path

1. **GroundingDINO** — open-vocabulary detection (Apache-2.0).
2. **SAM2** — production segmentation option (Apache-2.0).
3. **GrabCut fallback** — CPU-safe segmentation when SAM2 is unavailable.
4. **Proxy GLB generation** — always creates a usable 3D blockout for every accepted item.
5. **TRELLIS** — preferred high-quality image-to-3D GPU replacement (MIT majority; audit its documented submodules).
6. **TripoSR** — fast single-image 3D reconstruction option (MIT).
7. **Hunyuan3D** — optional texture/PBR enhancement path; verify the exact model/release license before redistributing model-derived assets.
8. **Blender ingestion** — imports proxies/high-quality replacements into the v0.6 material system and renders a QA gallery.

## Important design rule

The scanner never blocks the build merely because the expensive GPU backend is absent.
Every detection receives a proxy GLB immediately. High-quality GPU outputs replace
those files later using the same stable item id.

## Outputs

- `scanner_manifest.json`
- `quality_queue.json`
- per-image detection preview
- RGBA crops + masks
- proxy GLBs
- Blender gallery scene/render
- optional GPU backend job manifests

## Reference prompts

bow, cherry, strawberry, lollipop, heart candy, heart lantern, candy sign,
market stall, cupcake tower, castle tower, candy tree, frosting rock, bridge,
candy bench, crystal, gumdrop, donut.
