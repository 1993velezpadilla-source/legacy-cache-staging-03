# Nacht Golden Reference — Xziel

Status: ACTIVE BENCHMARK  
Internal map id: `nazi_zombie_prototype`  
Purpose: isolate engine defects from asset defects by validating Xziel against one coherent, known Zombies map.

## Two immutable tracks

### GOLDEN
The reference implementation. Once a subsystem matches the reference and passes device QA, do not redesign it here. GOLDEN is the control sample.

### LAB
A copy of GOLDEN used for experiments: Xziel zombie models, animation experiments, lighting changes, VFX, hit reactions, weapon presentation, new gameplay, etc. LAB may break; GOLDEN must remain reproducible.

## Required validation layers

1. map geometry and scale
2. collision and playable bounds
3. UVs and material assignment
4. texture sampling, mipmaps and compression
5. lighting, fog and sky
6. environmental FX
7. first-person arms and weapon presentation
8. weapon fire/reload/swap timing
9. spatial and gameplay audio
10. zombie model/animation playback
11. pathing, window approach and barricade interaction
12. round progression and spawn pacing
13. high-round CPU/GPU/memory stress
14. Android thermal/performance stability

A visual or gameplay layer is not marked PASS because a build succeeds. It needs runtime evidence.

## Reference sources

Primary public reference:
- CallOfDutyModding/call_of_duty_world_at_war_mod_tools
- original map-tool asset manifest: `zone_source/nazi_zombie_prototype.csv`
- original gameplay script: `raw/maps/nazi_zombie_prototype.gsc`
- original FX script: `raw/maps/nazi_zombie_prototype_fx.gsc`

These files identify the original Nacht dependency graph: BSP, scripts, weapons, sound banks, FX, skybox and viewmodel references.

## Asset rule

Do not commit retail-extracted Call of Duty payloads or disguise them under random names. Any external binary asset must have recorded provenance and redistribution permission.

The benchmark may ingest owner-supplied licensed/local assets without committing those payloads to this repository. Publicly released Mod Tools content must remain traceable to its source/EULA.

## Acceptance rule

GOLDEN becomes the engine control only when the same build demonstrates:
- stable geometry with no mesh corruption;
- correct UV/material mapping;
- expected near/far texture behavior;
- stable lighting/fog/FX;
- working movement, firing and reload;
- zombies spawning, navigating, attacking and interacting with barriers;
- round escalation without logic collapse;
- stress profiles completing without crash, runaway memory growth or catastrophic frame collapse.

See `stress_profiles.json` and `reference_manifest.json`.
