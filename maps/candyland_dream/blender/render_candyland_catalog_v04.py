"""Render one catalog image per visible Candyland ENV/PROPS mesh."""
import bpy, json, os, re
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
        visual.extend(o for o in c.objects if o.type=="MESH" and not o.hide_render)
visual=sorted(visual,key=lambda o:o.name.lower())
if not (30 <= len(visual) <= 140):
    raise RuntimeError(f"Expected 30-140 visible ENV/PROPS meshes, got {len(visual)}")

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

original={o.name:o.hide_render for o in visual}
assets=[]
try:
    for o in visual:
        for other in visual:
            other.hide_render=True
        o.hide_render=False
        bpy.context.view_layer.update()
        radius=frame(o)
        image=f"{len(assets)+1:02d}_{safe(o.name)}.png"
        scene.render.filepath=str(OUT/image)
        bpy.ops.render.render(write_still=True)
        assets.append({
            "index":len(assets)+1,
            "name":o.name,
            "collection":next((c.name for c in o.users_collection if c.name in ("ENV","PROPS")),None),
            "image":image,
            "location_m":[round(v,4) for v in o.location],
            "dimensions_m":[round(v,4) for v in o.dimensions],
            "triangles":tri_count(o),
            "frame_radius_m":round(radius,4)
        })
finally:
    for o in visual:
        o.hide_render=original[o.name]

manifest={
    "version":"0.5.1",
    "status":"CATALOG_RENDERED",
    "source_blend":"candyland_dream_v03.blend",
    "asset_count":len(assets),
    "render_size_px":[768,768],
    "background":"transparent",
    "assets":assets
}
(OUT/"catalog_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(json.dumps({"status":"CATALOG_RENDERED","asset_count":len(assets)}))
