# Candyland Dream — GitHub Free Asset / Blender Tool Audit

Date: 2026-09-23

This audit records external GitHub resources reviewed for the Candyland Dream map. Only repositories with an explicit redistribution-compatible license should be used in production.

## 1. SkywolfGameStudios/CC0Tree — APPROVED + INTEGRATED
Repository: https://github.com/SkywolfGameStudios/CC0Tree
License: CC0-1.0 / public-domain dedication.
Usefulness: lightweight low-poly FBX props suitable for Blender/game-runtime import.

Integrated in Candyland v0.4:
- SM_Tree_Rounded.fbx
- SM_Pine_Tree.fbx
- SM_WateringCan.fbx
- SM_TrashCan.fbx

The Blender report records the exact raw source URL and SHA-256 of every downloaded file.

## 2. KayKit-Game-Assets/KayKit-Restaurant-Bits-1.0 — APPROVED CANDIDATE
Repository: https://github.com/KayKit-Game-Assets/KayKit-Restaurant-Bits-1.0
License: CC0.
Repository README states 140+ low-poly optimized 3D models, free for personal/commercial use with no attribution required, supplied as OBJ, FBX and glTF.
Usefulness for Candyland: food props, serving props, kitchen/restaurant dressing, plates/ingredients and other recognizable objects that can be recolored or scaled for giant-food scenery.

Not yet bundled into the v0.4 runtime.

## 3. ranjian0/building_tools — APPROVED TOOLING CANDIDATE
Repository: https://github.com/ranjian0/building_tools
License: MIT.
Usefulness: procedural building generation in Blender; repository documents Blender 4.0 compatibility.
Good fit for generating more complete candy houses, shops and structural shells.

Not bundled as a runtime dependency in v0.4.

## Selection policy
- Prefer CC0 for redistributable models/textures.
- Prefer MIT/BSD/Apache for reusable scripts/add-ons when practical.
- Record source + license + version/commit before bundling.
- Do not use a model merely because a repository says "free" when the actual license is missing or unclear.
- Keep third-party runtime dependencies minimal; vendor only when license and project policy allow it.
