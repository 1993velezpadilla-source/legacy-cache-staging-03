# Candyland Dream v0.2

Status: PREPARED_NOT_EXECUTED

This pass extends the starter map without claiming Blender, engine, GPU, or mobile execution.

## Added
- Reusable lollipop prop factory.
- Explicit ENV, PROPS, COLLISION, NAV, and GAMEPLAY collections.
- Collision proxies for the chocolate river and lollipop trunks.
- Ordered navigation markers along the main route.
- Toggleable castle gate blocker metadata.
- Runtime collision/navigation manifest.
- v0.2 Blender generator that saves `candyland_dream_v02.blend`.

## Execution order
1. Run `blender -b --python blender/build_candyland_v02.py`.
2. Open `candyland_dream_v02.blend` and inspect gameplay-height sightlines.
3. Verify the 1.2 m player-clearance rule along the 5 m main path.
4. Confirm marshmallow stones provide a readable river crossing.
5. Toggle the castle gate and verify both locked/unlocked traversal.
6. Export GLB and validate scale/materials/collision naming in the target engine.
7. Run Android/mobile performance validation.

## Acceptance target
Spawn, Candy Plaza, Lollipop Forest, Chocolate River, and Cupcake Castle must remain readable, navigable, and inside the 96 m x 72 m footprint.

Runtime truth: all execution-dependent checks remain PREPARED_NOT_EXECUTED until a real runtime reports success.
