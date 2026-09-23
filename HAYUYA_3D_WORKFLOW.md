# Hayuya 3D / Hunyuan3D Workflow

Within this project, **Hayuya 3D** means the Hunyuan3D-style image-to-3D workflow used to turn approved reference images into a usable 3D asset, normally ending in GLB plus validation/previews.

Requests such as:
- "usa Hayuya"
- "haz este modelo con Hayuya 3D"
- "pasa esta imagen a 3D"
- "haz el GLB"

should use this workflow when an executable compatible runtime is actually available.

## Runtime check
Before saying generation started/completed, verify the current session can really execute the image-to-3D runtime.

If unavailable:
- do not pretend it is running;
- prepare references, prompts/config, measurements and manifests here;
- mark the job `PREPARED_NOT_EXECUTED`;
- state which runtime connection is missing.

## Asset package
Use:
`models/hayuya/<asset-name>/`

Recommended:
- `source/`
- `raw/`
- `processed/`
- `textures/`
- `previews/`
- `measurements.json`
- `PROVENANCE.md`
- `STATUS.md`

## Blender finishing
When Blender execution is available, use it for scale normalization, cleanup, normals, UV/material repair, texture hookup, LOD/decimation, rigging, animation retarget/bake, pivots, collisions/helper geometry, GLB export and review renders.

Store Blender sources/derived scripts in `blender/` or the asset package.

## Validation
Before calling a model done, verify import/open, dimensions, orientation, textures, completeness/silhouette, runtime usability, provenance and previews. Animated models also require skeleton/clip/retarget/bake status.
