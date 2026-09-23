"""Candyland Dream v0.7 Realism + Scanner Integration.

Executes v0.6, consumes CandyAssetScanner queue, adds scanner-driven hero assets,
improves PBR response on focal objects, then re-renders/re-exports the real map.
"""
from pathlib import Path
import bpy, json, math, os
from mathutils import Vector

# v0.7 is the only pass that needs final beauty renders. Older inherited
# generators still build all geometry/materials/metadata but skip redundant shots.
os.environ["CANDY_DEFER_INTERMEDIATE_RENDERS"]="1"

BASE=Path(__file__).with_name("build_candyland_v06.py")
exec(compile(BASE.read_text(encoding="utf-8"),str(BASE),"exec"),globals())

QUEUE=Path(os.environ.get("CANDY_SCANNER_QUEUE","candyland/scanner/asset_queue.json"))
queued=[]
if QUEUE.exists():
    queued=[a["class"] for a in json.loads(QUEUE.read_text()).get("assets",[])]

def has(cls): return cls in queued

def pbr_detail_mat(name,base,rough=.18,coat=.85,bump_strength=.08,scale=24.0,sheen=.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*base,1); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new("ShaderNodeOutputMaterial")
    bs=nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value=(*base,1)
    bs.inputs["Roughness"].default_value=rough
    if "Coat Weight" in bs.inputs: bs.inputs["Coat Weight"].default_value=coat
    if "Coat Roughness" in bs.inputs: bs.inputs["Coat Roughness"].default_value=max(.03,rough*.35)
    if "Sheen Weight" in bs.inputs: bs.inputs["Sheen Weight"].default_value=sheen
    noise=nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value=scale; noise.inputs["Detail"].default_value=4.0; noise.inputs["Roughness"].default_value=.58
    bump=nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value=bump_strength; bump.inputs["Distance"].default_value=.035
    nt.links.new(noise.outputs["Fac"],bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"],bs.inputs["Normal"])
    nt.links.new(bs.outputs["BSDF"],out.inputs["Surface"])
    return m

SATIN=pbr_detail_mat("V07_Satin_Bow",(1.0,.50,.72),.24,.55,.025,42,.55)
SUGAR_RED=pbr_detail_mat("V07_Sugar_Cherry",(.83,.012,.085),.10,1.0,.035,55,0)
SUGAR_PINK=pbr_detail_mat("V07_Sugar_Pink",(1.0,.20,.56),.11,1.0,.04,52,0)
FROST_REAL=pbr_detail_mat("V07_Real_Frosting",(1.0,.91,.87),.38,.28,.10,8,0)
WAFER_REAL=pbr_detail_mat("V07_Real_Wafer",(.78,.43,.16),.46,.18,.16,12,0)
GLASS_HEART=new_principled("V07_Heart_Glass",(1.0,.18,.55),rough=.07,coat=1.0,emission=(1.0,.16,.50),emission_strength=1.6)

def mat_on(obj,material):
    if obj and obj.type=="MESH":
        obj.data.materials.clear(); obj.data.materials.append(material)
    return obj

def soften(obj,width=.10,subdiv=False):
    if not obj or obj.type!="MESH": return obj
    add_bevel(obj,width,4)
    for p in obj.data.polygons: p.use_smooth=True
    if subdiv and len(obj.data.polygons)<20000:
        s=obj.modifiers.new("V07_Subdivision","SUBSURF"); s.levels=1; s.render_levels=1
    return obj

scanner_objects=[]

# Scanner-driven satin bow set.
if has("satin_bow"):
    for i,(loc,s) in enumerate([
        ((-34,-21.9,6.0),1.05),((-12,-8.0,4.0),.78),((28,18.0,8.5),1.20),
        ((18,4.8,3.7),.72)
    ]):
        o=bow(f"V07_SCAN_Bow_{i}",loc,s,SATIN)
        if o: scanner_objects.append(o)

# Cherries and strawberries get detailed micro-bump materials.
if has("cherry"):
    for i,(x,y,z,s) in enumerate([
        (-18,-14,1.05,.75),(-8,-13,1.0,.62),(22,18,1.0,.72),(34,20,1.0,.72),(28,24,18.4,.78)
    ]):
        o=sphere(f"V07_SCAN_Cherry_{i}",(x,y,z),s,SUGAR_RED,PROPS,segments=32)
        soften(o,.045,True); scanner_objects.append(o)
        stem=cyl(f"V07_SCAN_CherryStem_{i}",(x+.15*s,y,z+.95*s),.05*s,1.05*s,GOLD_PREMIUM,PROPS,vertices=12,rot=(0,math.radians(-16),0))
        scanner_objects.append(stem)

if has("strawberry"):
    for i,(loc,s) in enumerate([
        ((-19,-8,1.1),.78),((10,8,1.0),.70),((37,15,1.15),.82),((40,29,1.1),.78)
    ]):
        o=make_strawberry(f"V07_SCAN_Strawberry_{i}",loc,s)
        mat_on(o,SUGAR_RED); soften(o,.04,True); scanner_objects.append(o)

# Heart lanterns/crystals along travel line.
if has("heart_lantern"):
    for i,(x,y) in enumerate([(-31,-23),(-21,-15),(-13,-6),(-5,1),(8,2),(20,10),(26,19)]):
        post=cyl(f"V07_SCAN_LampPost_{i}",(x,y,1.9),.11,3.8,GOLD_PREMIUM,PROPS,vertices=16)
        gem=heart(f"V07_SCAN_LampHeart_{i}",(x,y,4.15),.45,GLASS_HEART,rot=(math.radians(90),0,0))
        scanner_objects += [post,gem]

if has("heart_crystal"):
    for i,(x,y,z) in enumerate([(24,14,1.6),(32,14,1.6),(21,23,1.6),(35,23,1.6)]):
        gem=heart(f"V07_SCAN_Crystal_{i}",(x,y,z),.72,IRIDESCENT,rot=(math.radians(90),0,0))
        scanner_objects.append(gem)

# Forest scanned lollipop family.
if has("lollipop_tree"):
    for i,(x,y,h,r,matl) in enumerate([
        (-44,12,6.8,1.30,HOT_PINK_GLOSS),(-38,19,7.6,1.45,LAVENDER_GLOSS),
        (-30,17,6.2,1.20,CYAN_GLOSS),(-24,28,8.0,1.55,BLUSH_GLOSS),
        (-16,24,6.5,1.25,MINT_GLOSS),(-12,32,7.2,1.35,HOT_PINK_GLOSS)
    ]):
        o=make_lollipop(f"V07_SCAN_Lollipop_{i}",(x,y),h,r,matl)
        soften(o,.035,False); scanner_objects.append(o)

# Plaza gets richer scanner-driven stalls and seating.
if has("market_stall"):
    for i,(x,y,accent) in enumerate([(-22,-10,BLUSH_GLOSS),(-3,-9,LAVENDER_GLOSS)]):
        o=make_market_stall(f"V07_SCAN_Stall_{i}",(x,y),.78,accent)
        soften(o,.075,False); scanner_objects.append(o)
        b=bow(f"V07_SCAN_StallBow_{i}",(x,y-1.55,3.62),.46,SATIN)
        if b: scanner_objects.append(b)

if has("candy_bench"):
    for i,(x,y,ang) in enumerate([(-18,-5,.25),(-7,-4,-.30),(-14,-18,.10)]):
        seat=cube(f"V07_SCAN_BenchSeat_{i}",(x,y,1.0),(1.75,.52,.18),SUGAR_PINK,PROPS,rot=(0,0,ang))
        back=cube(f"V07_SCAN_BenchBack_{i}",(x,y+.42,1.75),(1.75,.14,.65),SATIN,PROPS,rot=(0,0,ang))
        scanner_objects += [seat,back]

# Castle scanned cupcake/tower family.
if has("cupcake_tower"):
    for i,(x,y,s) in enumerate([(18,25,.70),(39,26,.72),(20,33,.58),(36,34,.60)]):
        o=make_cupcake_house(f"V07_SCAN_CupcakeTower_{i}",(x,y),s)
        soften(o,.06,False); scanner_objects.append(o)

# Signs.
if has("signpost"):
    for i,(x,y) in enumerate([(-31,-18),(-18,-8),(12,2),(22,13)]):
        post=cyl(f"V07_SCAN_SignPost_{i}",(x,y,1.8),.11,3.6,GOLD_PREMIUM,PROPS,vertices=14)
        for k,(z,rot,matl) in enumerate([(2.8,-.10,SUGAR_PINK),(3.45,.12,SATIN),(4.1,-.06,LAVENDER_GLOSS)]):
            board=cube(f"V07_SCAN_SignBoard_{i}_{k}",(x+.42,y,z),(1.25,.13,.31),matl,PROPS,rot=(0,0,rot))
            scanner_objects.append(board)
        scanner_objects.append(post)

# Frosting cliffs and wafer bridge detail.
if has("frosting_rock"):
    for i,(x,y,s) in enumerate([(-45,-25,1.2),(-48,0,1.25),(42,5,1.15),(42,31,1.15)]):
        o=make_frosting_cliff(f"V07_SCAN_FrostRock_{i}",(x,y),(4.8*s,3.2*s,2.4*s),FROST_REAL)
        soften(o,.08,False); scanner_objects.append(o)

if has("wafer_bridge_decor"):
    for i in range(10):
        x=13.5+i*1.0
        plank=cube(f"V07_SCAN_WaferPlank_{i}",(x,5.0,1.10),(.42,2.7,.20),WAFER_REAL,ENV)
        scanner_objects.append(plank)
    for side in (-1,1):
        rail=cyl(f"V07_SCAN_WaferRail_{side}",(18,5+side*2.85,2.15),.12,10.0,PEARL_FROST,ENV,vertices=16,rot=(0,math.radians(90),0))
        scanner_objects.append(rail)

# Per-object provenance flags.
for o in scanner_objects:
    try:
        o["scanner_source"]="approved_overview"
        o["scanner_pipeline"]="CandyAssetScanner_v07"
    except Exception: pass

# Re-render map and scanner integration close-up.
scene=bpy.context.scene
shots=[
    ("candyland_iso",(92,-104,80),(0,3,4)),
    ("candyland_spawn_view",(-49,-46,13),(-20,-8,4)),
    ("candyland_castle_view",(58,-1,30),(28,24,7)),
    ("candyland_plaza_view",(-34,-34,18),(-12,-10,3)),
    ("candyland_forest_view",(-58,2,18),(-29,23,4.5)),
    ("candyland_river_view",(43,-20,18),(18,5,2.5)),
    ("candyland_gloss_closeup",(-24,-26,8),(-11,-10,2.4)),
    ("candyland_scanner_integration",(47,-18,16),(20,11,3.2)),
]
for name,loc,target in shots:
    cam.location=loc; look_at(cam,target)
    scene.render.filepath=str(OUT/f"{name}.png"); bpy.ops.render.render(write_still=True)

# Re-export enriched real map.
for o in bpy.context.scene.objects: o.select_set(False)
visual=[]
for c in (ENV,PROPS):
    for o in c.objects:
        if o.type=="MESH" and not o.hide_render:
            o.select_set(True); visual.append(o)
if visual:
    bpy.context.view_layer.objects.active=visual[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT/"candyland_dream_v03.glb"),export_format="GLB",use_selection=True,export_apply=True)

for o in bpy.context.scene.objects: o.select_set(False)
props=[o for o in PROPS.objects if o.type=="MESH" and not o.hide_render]
for o in props: o.select_set(True)
if props:
    bpy.context.view_layer.objects.active=props[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT/"candy_props_v03.glb"),export_format="GLB",use_selection=True,export_apply=True)

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"candyland_dream_v03.blend"))

report_path=OUT/"blender_report.json"
report=json.loads(report_path.read_text()) if report_path.exists() else {}
report.update({
    "version":"0.7.0",
    "vision_pass":"REALISM_AND_SCANNER_INTEGRATION",
    "scanner_queue_classes":queued,
    "scanner_generated_object_count":len(scanner_objects),
    "visual_meshes":len(visual),
    "visual_triangles":sum(tri_count(o) for o in visual),
    "beauty_renders":[x[0]+".png" for x in shots],
    "scanner_integration_render":"candyland_scanner_integration.png"
})
report_path.write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
