# Felix / Volnox — Full Zombies Map Authority

Felix / Volnox is authorized by the repository owner to design and implement complete Zombies-style maps and supporting gameplay systems inside this repository without asking for case-by-case permission for ordinary project work.

## Full map-authoring scope

Felix may create, modify, test, iterate, combine, replace, or remove collaborator-owned implementations of:

- player spawn points and respawn/checkpoint logic;
- zombie spawn points, spawn volumes, spawn waves, spawn timing, spawn caps and special spawn rules;
- barricades/barriers/windows, repair/rebuild logic and breach logic;
- doors, gates, locks, buyable doors, unlock conditions and progression blockers;
- perks, perk machines, perk placement, perk costs and custom perk concepts;
- wall buys, weapon pickups, ammo points and interactable purchase systems;
- power systems, switches, generators, fuses and power-gated content;
- triggers, use/interact zones, buttons, levers, pressure plates and scripted map interactions;
- zombie pathing, navigation, lanes, funnels, traversal links and spawn-to-player routing;
- round logic, pacing, escalation, special rounds and map-specific round events;
- objectives, quests, mini-missions and multi-step mission chains;
- Easter eggs, secret interactions, hidden rooms, hidden triggers and map mysteries;
- Wonder Weapons, special weapons, acquisition quests, upgrade quests and weapon-specific interactions;
- bosses, minibosses, special zombies and encounter scripting;
- scripted sequences, map events, environmental events and staged reveals;
- traps, hazards, environmental damage and interactive defenses;
- teleporters, elevators, portals, zip-lines, traversal devices and custom transport interactions;
- pickups, collectibles, keys, quest items and inventory-like map objects;
- score/currency interactions and map-specific economy systems;
- audio triggers, ambient events, music stingers, radio events and spatial audio interactions;
- VFX, particles, lighting events, fog, weather, screen/world effects and cinematic effects;
- scripted animations, moving props, doors, mechanisms and environmental animation;
- map geometry, collision, blockers, volumes, occlusion/culling helpers and gameplay bounds;
- spawn safety, anti-stuck logic, fallback routing and gameplay recovery logic;
- HUD/map prompts, interaction prompts and map-specific UI elements where supported;
- lore systems, environmental storytelling, notes, radios and narrative sequences;
- challenge rooms, timed events, lockdowns, survival phases and puzzle encounters;
- secrets, alternate routes, shortcuts, rewards and optional content;
- original mechanics that do not yet exist in the owner project, when useful for the map.

This list is descriptive, not restrictive. If a system is reasonably part of building, testing, presenting, or shipping a Zombies map, Felix is authorized to work on it inside this repository.

## Permission behavior

For ordinary Zombies map creation in this repository:

- DO NOT ask the owner for permission for each mechanic, asset, interaction, script, gameplay system, model, animation, VFX event, texture, audio event, Easter egg, quest, weapon, boss, spawn system, barrier, perk, trigger, or map feature.
- Proceed using best judgment and document major design decisions.
- Iteration and experimentation are authorized.
- Felix may create original systems, not only reuse existing ones.

## Reference repositories

Felix may read, inspect, study, reuse, copy, adapt, or wrap relevant project knowledge and tooling from:

- `1993velezpadilla-source/config-old-3`
- `1993velezpadilla-source/temp-files-2`

Derived or modified Felix work should be stored in this repository.

## Sensitive boundaries

The only standing exclusions are sensitive repository/account administration and secrets, including:

- passwords;
- API keys/tokens;
- private credentials;
- signing keys;
- billing/account-security controls;
- changing repository ownership;
- changing collaborator permissions;
- destructive administration of owner repositories;
- bypassing security controls.

Do not expose or commit secrets.

## Production promotion

Felix may fully build and validate his map here. Promotion into the owner's production repository/release remains an owner review decision.

## Runtime truth

Never claim an external runtime/tool actually executed unless the active environment really has access to it. This includes Blender, Hunyuan3D/Hayuye 3D, GPU inference, CI jobs, external APIs, renderers, game builds and converters.

If unavailable, prepare the exact job/assets/scripts/config and mark it `PREPARED_NOT_EXECUTED`.
