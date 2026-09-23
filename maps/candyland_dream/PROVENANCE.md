# Candyland Dream Provenance

## Source concept
The initial art direction comes from the Candyland Dream concept board generated in this conversation. It is a visual design reference, not a production game asset.

## Repository references
Reusable technical knowledge may be consulted from:
- 1993velezpadilla-source/config-old-3
- 1993velezpadilla-source/temp-files-2

All new Felix/Volnox deliverables belong in legacy-cache-staging-03.

## External GitHub assets used by the v0.4 Blender build
Source: `SkywolfGameStudios/CC0Tree`
License: Creative Commons Zero v1.0 Universal (CC0-1.0), public-domain dedication.

The automated Blender build downloads these public FBX assets directly from the source repository:
- `SM_Tree_Rounded.fbx`
- `SM_Pine_Tree.fbx`
- `SM_WateringCan.fbx`
- `SM_TrashCan.fbx`

Each downloaded file is recorded in `blender_report.json` with its source URL, CC0 status, and SHA-256 digest.


## Additional CC0 meshes integrated by the v0.5 detail pass
Source: `KayKit-Game-Assets/KayKit-Halloween-Bits-1.0`
License: CC0-1.0.
- `bench.fbx` used as a recolored CandyBench.

Source: `KayKit-Game-Assets/KayKit-Restaurant-Bits-1.0`
License: CC0-1.0.
- `crate_buns.fbx` used as a recolored CookieCrate.

Both repositories explicitly permit personal, educational and commercial use, with attribution optional.

## Free Blender tooling evaluated
`ranjian0/building_tools` was reviewed as an optional procedural-building helper. It is MIT licensed and reports Blender 4.0 compatibility. It is not bundled into the Candyland runtime in this pass, so the map does not take a dependency on the add-on.

## Redistribution rule
Only assets with verified redistribution-compatible licensing may be bundled or fetched by production workflows. Unknown-license repositories are references only until their license is verified.

## Execution status
The v0.4 build is designed to run in the repository's Candyland five-agent GitHub Actions pipeline. Runtime claims must come from the resulting workflow evidence and artifacts.
