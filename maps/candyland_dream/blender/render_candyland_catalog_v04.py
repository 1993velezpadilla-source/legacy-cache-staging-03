"""Render a scalable deduplicated catalog of visible Candyland ENV/PROPS meshes.

v0.8 catalog strategy:
- Never fail merely because the world gained more placed objects.
- Group repeated numbered instances into stable asset families.
- Render one representative per family.
- Preserve source-object counts and family membership in the manifest.
- Keep an absolute sanity ceiling only for pathological/corrupt scenes.
"""
import bpy, json, os, re
from collections import defaultdict
from pathlib import Path
from mathutils import Vector

OUT=Path(os.environ.get("CANDY_CATALOG_OUT","candyland/catalog"))
OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
scene.render.resolution_x=768
scene.render.resolution_y=768
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.render.film_transparent=True
try:
    scene.render.engine="BLENDER_EEVEE_NEXT"
except Exception:
    scene.render.engine="BLENDER_EEVEE"

visual=[]
for cname in ("ENV","PROPS"):
    c=bpy.data.collections.get(cname)
    if c:
        visual.extend(
            o for o in c.objects
            if o.type=="MESH" and not o.hide_render and not o.get("catalog_skip",False)
        )
visual=sorted(visual,key=lambda o:o.name.lower())

if len(visual) < 30:
    raise RuntimeError(f"Expected at least 30 visible ENV/PROPS meshes, got {len(visual)}")
if len(visual) > 5000:
    raise RuntimeError(f"Scene sanity guard: refusing to catalog {len(visual)} meshes (>5000)")

cam=scene.camera
if cam is None:
    bpy.ops.object.camera_add()
    cam=bpy.context.object
    scene.camera=cam
cam.data.clip_end=2000

def look_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

def tri_count(o):
    o.data.calc_loop_triangles()
    return len(o.data.loop_triangles)

def frame(o):
    pts=[o.matrix_world @ Vector(c) for c in o.bound_box]
    center=sum(pts,Vector((0,0,0)))/8.0
    radius=max(max((p-center).length for p in pts),0.75)
    direction=Vector((1.35,-1.6,1.15)).normalized()
    cam.location=center+direction*max(4.5,radius*3.35)
    cam.data.lens=58 if radius < 8 else 52
    look_at(cam,center)
    return radius

def safe(name):
    return re.sub(r"[^A-Za-z0-9_.-]+","_",name).strip("_")

def normalized_name(name):
    # Blender suffixes (.001) and generated trailing numeric instance indices.
    x=re.sub(r"\.\d{3}$","",name)
    x=re.sub(r"(?:_\d+)+$","",x)
    return x or name

def material_signature(o):
    return tuple(sorted(m.name for m in o.data.materials if m))

def family_key(o):
    explicit=o.get("catalog_family")
    if explicit:
        return f"explicit::{explicit}"
    # Name family + material signature avoids collapsing color/material variants
    # while still deduplicating repeated numbered placements.
    return "auto::"+normalized_name(o.name)+"::"+"|".join(material_signature(o))

families=defaultdict(list)
for o in visual:
    families[family_key(o)].append(o)

# Representative: highest triangle count, then stable name.
representatives=[]
for key,members in families.items():
    rep=sorted(members,key=lambda o:(-tri_count(o),o.name.lower()))[0]
    representatives.append((key,rep,sorted(m.name for m in members)))
representatives.sort(key=lambda x:(normalized_name(x[1].name).lower(),x[1].name.lower()))

original={o.name:o.hide_render for o in visual}
assets=[]
try:
    for key,o,members in representatives:
        for other in visual:
            other.hide_render=True
        o.hide_render=False
        bpy.context.view_layer.update()
        radius=frame(o)
        image=f"{len(assets)+1:03d}_{safe(normalized_name(o.name))}.png"
        scene.render.filepath=str(OUT/image)
        bpy.ops.render.render(write_still=True)
        assets.append({
            "index":len(assets)+1,
            "family_key":key,
            "family_name":normalized_name(o.name),
            "representative":o.name,
            "instance_count":len(members),
            "members":members,
            "collection":next((c.name for c in o.users_collection if c.name in ("ENV","PROPS")),None),
            "image":image,
            "location_m":[round(v,4) for v in o.location],
            "dimensions_m":[round(v,4) for v in o.dimensions],
            "triangles":tri_count(o),
            "materials":list(material_signature(o)),
            "frame_radius_m":round(radius,4)
        })
finally:
    for o in visual:
        o.hide_render=original[o.name]

manifest={
    "version":"0.8.0",
    "status":"CATALOG_RENDERED",
    "catalog_mode":"DEDUPLICATED_ASSET_FAMILIES",
    "source_blend":"candyland_dream_v03.blend",
    "source_object_count":len(visual),
    "asset_count":len(assets),
    "family_count":len(assets),
    "deduplicated_instance_count":len(visual)-len(assets),
    "render_size_px":[768,768],
    "background":"transparent",
    "assets":assets
}
(OUT/"catalog_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(json.dumps({
    "status":"CATALOG_RENDERED",
    "source_object_count":len(visual),
    "family_count":len(assets),
    "deduplicated_instance_count":len(visual)-len(assets)
}))
