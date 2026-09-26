# WaW Mod Tools — Nacht Golden Reference Audit

Date: 2026-09-25

## Critical finding

The public Call of Duty: World at War Mod Tools repository does **not** contain the full editable Nacht map source `nazi_zombie_prototype.map`.

The `map_source` tree contains 447 entries and includes many Zombies prefabs and tutorial/sample maps, but not the complete Nacht level source.

Therefore the Mod Tools alone cannot provide a complete 1:1 Nacht environment.

## What the Mod Tools do provide and is useful for Xziel validation

### Original weapon model/material data
Examples found in `model_export`:

- Thompson first-person model exports
- Thompson world LOD0/LOD1/LOD2 exports
- Thompson color/normal/specular-style texture sets
- MG42 first-person model exports
- Colt texture sets
- German and US viewmodel texture sets

Notable examples:
- `american/weapons/SMGs/thompson/viewmodel_usa_thompson_smg.XMODEL_EXPORT`
- `american/weapons/SMGs/thompson/weapon_usa_thompson_smg_LOD0.XMODEL_EXPORT`
- `american/weapons/SMGs/thompson/w_tommy_C.tga`
- `american/weapons/SMGs/thompson/w_tommy_N.tga`
- `american/weapons/SMGs/thompson/w_tommy_S.tga`
- `viewmodels/german/mg42/viewmodel_mg42.XMODEL_EXPORT`
- `viewmodels/textures/viewmodel_usa_marine_zombie_c.tga`
- `viewmodels/textures/viewmodel_usa_marine_zombie_n.tga`

### Original weapon animation data
Examples found in `xanim_export/viewmodel/US/thompson`:

- idle
- fire
- fire ADS
- reload
- reload empty
- melee
- pullout
- putaway
- ADS up/down
- last shot

These are suitable for validating Xziel's skeletal/viewmodel animation conversion without relying on NZ:P replacement content.

### Zombies-specific map prefabs
The public `map_source` tree includes Zombies prefabs for:

- barriers
- windows
- door barricades
- wall-buy weapon points
- treasure chest
- player spawners
- dog/spawn helpers
- traversal/window nodes
- wall-break pieces
- vending/perk prefabs

Examples:
- `_prefabs/zombiemode/adam_zombie_barrier.map`
- `_prefabs/zombiemode/window_med.map`
- `_prefabs/zombiemode/weapon_kar98.map`
- `_prefabs/zombiemode/weapon_thompson.map`
- `_prefabs/zombiemode/treasure_chest.map`
- `_prefabs/traverse/window_negotiate_node_extended.map`

## What remains missing for an actual full Nacht 1:1 control

- complete editable Nacht environment source
- complete Nacht-specific geometry/layout payload
- full Nacht-specific material/texture set bound to that geometry
- complete retail zombie actor/model/animation set used in Nacht
- complete Nacht retail sound payloads
- compiled retail level payload sufficient to recover all of the above

## Benchmark implication

Do not use an NZ:P/Quake Nacht recreation as the GOLDEN visual authority.

The GOLDEN benchmark should only mark a layer as `ORIGINAL_WAW_REFERENCE` when its source is demonstrably original WaW content.

Public Mod Tools assets can be used to validate:
- first-person weapon model import
- material channel handling
- weapon animation conversion
- barrier/window gameplay geometry
- wall-buy interaction placement
- selected Zombies prefabs

A complete 1:1 Nacht environment still requires a legitimate source for the missing retail level content.
