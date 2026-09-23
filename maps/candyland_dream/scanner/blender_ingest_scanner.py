"""Import CandyAssetScanner proxy GLBs into a copy of the Candyland scene.

Usage:
  blender --background BASE.blend --python blender_ingest_scanner.py -- SCANNER_DIR OUTPUT.blend
"""
import bpy, json, math, sys
from pathlib import Path

argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(argv)<2: raise SystemExit("Need SCANNER_DIR OUTPUT_BLEND")
root=Path(argv[0]); out=Path(argv[1])
manifest=json.loads((root/"scanner_manifest.json").read_text())
col=bpy.data.collections.get("SCANNED_PROXIES") or bpy.data.collections.new("SCANNED_PROXIES")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)

# v0.6 material mapping; fall back safely if a material is absent.
mat_pref={
 "bow":"V06_Bubblegum_Gloss","cherry":"V06_Cherry_Candy_Shell","strawberry":"V06_Cherry_Candy_Shell",
 "lollipop":"V06_Hot_Pink_Gloss","heart candy":"V06_Heart_Gem","heart lantern":"V06_Heart_Gem",
 "crystal":"V06_Iridescent_Sugar_Glaze","candy tree":"V06_Blush_Gloss",
 "bridge":"V06_Gold_Trim","market stall":"V06_Bubblegum_Gloss","cupcake tower":"V06_Pearl_Frosting",
 "castle tower":"V06_Lavender_Gloss","frosting rock":"V06_Cream_Frosting"
}
items=[x for im in manifest["images"] for x in im["items"]]
# Show a curated proxy gallery outside the playable map first.
cols=8; spacing=4.0
for i,item in enumerate(items[:48]):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(root/item["proxy_glb"]))
    new=[o for o in bpy.data.objects if o not in before]
    meshes=[o for o in new if o.type=="MESH"]
    x=(i%cols-cols/2)*spacing
    y=48+(i//cols)*spacing
    for o in meshes:
        o.location.x+=x; o.location.y+=y
        o.name=f'SCAN_{item["id"]}_{o.name}'
        o["scanner_label"]=item["label"]; o["scanner_score"]=float(item["score"])
        m=bpy.data.materials.get(mat_pref.get(item["label"],"V06_Bubblegum_Gloss"))
        if m:
            o.data.materials.clear(); o.data.materials.append(m)
        for old in list(o.users_collection): old.objects.unlink(o)
        col.objects.link(o)

# add camera for scanner gallery
bpy.ops.object.camera_add(location=(0,72,42))
cam=bpy.context.object; cam.name="Scanner_Gallery_Camera"; bpy.context.scene.camera=cam
from mathutils import Vector
cam.rotation_euler=(Vector((0,55,4))-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.lens=52
scene=bpy.context.scene
scene.render.resolution_x=1280; scene.render.resolution_y=720; scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.filepath=str(out.with_name("scanner_proxy_gallery.png"))
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
print(json.dumps({"status":"BLENDER_SCANNER_INGEST_OK","imported_items":min(len(items),48),"output":str(out)},indent=2))
