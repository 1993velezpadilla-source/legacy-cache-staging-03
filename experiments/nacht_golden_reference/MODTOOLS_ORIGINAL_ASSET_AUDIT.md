# Nacht GOLDEN — Original WaW Mod Tools Asset Audit

This audit intentionally distinguishes the **original World at War source assets published with the Mod Tools** from NZ:P/Quake substitutes.

## What is actually present in the Mod Tools repository

Confirmed original-source content includes:

- `raw/maps/nazi_zombie_prototype.gsc`
- `raw/maps/nazi_zombie_prototype_fx.gsc`
- `raw/maps/createart/nazi_zombie_prototype_art.gsc`
- `raw/clientscripts/createfx/nazi_zombie_prototype_fx.csc`
- `raw/soundaliases/nazi_zombie_prototype.csv`
- Nacht material/loadscreen references
- Zombies barrier/window/weapon prefabs under `map_source/_prefabs/zombiemode/`
- original weapon source/export assets, including XMODEL_EXPORT/Maya/texture channels for multiple WaW weapons
- original weapon WAVs and foley
- original zombie character/material/AI definitions
- original zombie/head/model reference images
- original viewmodel zombie arm textures
- original zombie FX/material/collision support assets

Examples verified in-tree:

### Thompson
- `model_export/american/weapons/SMGs/thompson/viewmodel_usa_thompson_smg.XMODEL_EXPORT`
- `model_export/american/weapons/SMGs/thompson/weapon_usa_thompson_smg_LOD0.XMODEL_EXPORT`
- `.../w_tommy_C.tga`
- `.../w_tommy_N.tga`
- `.../w_tommy_S.tga`
- original fire/foley WAVs under `raw/sound/SFX/weapon/SMG/Thompson/`

### Colt
- original C/G/N/S texture channels are present
- original fire/reload/foley WAVs are present
- material and collision definitions are present

### Zombies
- `raw/character/char_ger_honorguard_zombies.gsc`
- `raw/character/char_ger_honorguard2_zombies.gsc`
- honor-guard zombie material families
- zombie head/body/gib reference assets
- zombie eye texture/detail-map assets
- zombie movement/traversal scripts and prefabs

### Viewmodel / Ray Gun
- `model_export/viewmodels/textures/viewmodel_usa_marine_zombie_c.tga`
- `model_export/viewmodels/textures/viewmodel_usa_marine_zombie_n.tga`
- Ray Gun material/collision definitions and original WAV set

## Important missing piece

The repository does **not** contain the complete `map_source/nazi_zombie_prototype.map` source map. It contains `nazi_zombie_tutorial.map`, Zombies prefabs, and Nacht scripts/FX/audio references.

Therefore:

- do **not** use the NZ:P map as the GOLDEN visual authority;
- use original WaW Mod Tools assets wherever they are present;
- treat missing Nacht world geometry as a separate acquisition/reconstruction problem;
- never claim a one-to-one map geometry pass until the actual original world geometry source is present or independently reconstructed and verified.

## GOLDEN authority order

1. Original WaW Mod Tools source assets
2. Original Nacht scripts/FX/audio manifests
3. Original WaW screenshots/video/reference for placement verification
4. Reconstruction only for pieces absent from the published Mod Tools
5. NZ:P/Quake content may be used only as gameplay/runtime reference, never as original visual authority

## Release rule

GOLDEN is internal benchmark material. Xziel public builds must not accidentally package third-party benchmark assets without an explicit release review.
