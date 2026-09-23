# Candyland Dream — Starter Map

Status: BLOCKOUT_PREPARED_NOT_EXECUTED
Owner workspace: legacy-cache-staging-03
Author: Felix / Volnox (XRP007)

Candyland Dream is a playful starter environment based on the supplied concept board: an oversized children's candy fantasy with a clear playable route from Spawn to Candy Plaza, Lollipop Forest, Chocolate River, and the Cupcake Castle destination.

## Build intent
- Small, readable starter map before larger expansion.
- Modular candy props for scalable production.
- Bright dreamlike presentation with room for a later tonal transition.
- Engine-neutral blockout first; runtime/export validation afterward.

## Route
Spawn / Start -> Candy Plaza -> Lollipop Forest
                           -> Chocolate River
                           -> Cupcake Castle (destination / initially gated)

## Runtime truth
This package is documentation plus a prepared Blender generator. No Blender, Hunyuan3D/GPU, renderer, engine, Android build, or GLB export execution is claimed until a real runtime reports success.

## Next execution
Run `blender -b --python blender/build_candyland_blockout.py` in an actual Blender runtime, inspect the scene, then validate collision/navigation and export previews/runtime geometry.
