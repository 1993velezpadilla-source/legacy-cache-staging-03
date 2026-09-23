"""Candyland Dream v0.3 executable Blender build.

Creates the playable blockout, a procedural candy prop pack, preview renders,
GLB exports, an editable .blend, and a machine-readable report.
"""
import bpy, json, math, os
from pathlib import Path
from mathutils import Vector

OUT=Path(os.environ.get("CANDY_OUT","candyland/out"))
OUT.mkdir(parents=True,exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def mat(name,color):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1.0)
    return m

PINK=mat("Candy_Ground",(0.96,0.55,0.72))
PATH=mat("Rainbow_Path",(0.95,0.35,0.55))
CHOCO=mat("Chocolate_River",(0.20,0.06,0.025))
GREEN=mat("Gummy_Green",(0.35,0.90,0.35))
RED=mat("Lollipop_Red",(1.0,0.15,0.35))
CREAM=mat("Castle_Cream",(1.0,0.82,0.55))
PURPLE=mat("Cupcake_Purple",(0.70,0.35,1.0))
WHITE=mat("Sugar_White",(0.96,0.96,1.0))

def col(name):
    c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c

ENV=col("ENV"); PROPS=col("PROPS"); COLLISION=col("COLLISION"); NAV=col("NAV"); GAMEPLAY=col("GAMEPLAY")

def move(o,c):
    for old in list(o.users_collection):
        old.objects.unlink(o)
    c.objects.link(o)

def cube(name,loc,scale,material=None,c=ENV,hide=False):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if material: o.data.materials.append(material)
    move(o,c); o.hide_render=hide
    return o

def cyl(name,loc,radius,depth,material=None,c=PROPS,vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    o=bpy.context.object; o.name=name
    if material: o.data.materials.append(material)
    move(o,c)
    return o

def sphere(name,loc,radius,material=None,c=PROPS,segments=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=12,radius=radius,location=loc)
    o=bpy.context.object; o.name=name
    if material: o.data.materials.append(material)
    move(o,c)
    return o

def look_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

def tri_count(o):
    if o.type!="MESH": return 0
    o.data.calc_loop_triangles()
    return len(o.data.loop_triangles)

cube("Candyland_Ground",(0,0,-1),(48,36,1),PINK)
route=[(-34,-25),(-25,-20),(-12,-10),(-20,3),(-28,18),(0,-2),(18,5),(28,24)]
for i,(x,y) in enumerate(route):
    cube(f"Path_{i:02d}",(x,y,0.25),(4,2.5,0.25),PATH)

cyl("Candy_Plaza",(-12,-10,0.2),8,0.5,CREAM,vertices=48)
cyl("Plaza_Center_Candy",(-12,-10,1.4),2.5,2.0,RED,vertices=48)

cube("Chocolate_River",(18,5,-0.25),(5,22,0.25),CHOCO)
for i,y in enumerate([-12,-4,4,12,20]):
    cyl(f"Marshmallow_{i:02d}",(18,y,0.4),1.7,0.7,WHITE,vertices=24)

forest=[(-38,10),(-31,27),(-22,12),(-16,25),(-40,28),(-8,21)]
for i,(x,y) in enumerate(forest):
    cyl(f"Lollipop_Stem_{i:02d}",(x,y,4),0.45,8,GREEN,vertices=16)
    cyl(f"Lollipop_Candy_{i:02d}",(x,y,8.5),2.2,1.0,RED,vertices=32)

cyl("Castle_Platform",(28,24,0.5),12,1.0,CREAM,vertices=48)
for i,(dx,dy,r,h) in enumerate([(-6,-5,2,8),(6,-5,2,8),(-6,5,2,10),(6,5,2,10),(0,0,3,14)]):
    cyl(f"Castle_Tower_{i:02d}",(28+dx,24+dy,h/2+1),r,h,PURPLE,vertices=32)

gate=cube("Castle_Gate_Blocker",(28,13,2.5),(4,0.5,2.5),CREAM,GAMEPLAY)
gate["role"]="toggle_gate"; gate["default_locked"]=True

asset_names=[]
for i,(x,y) in enumerate([(-5,8),(8,18),(5,-20),(-35,-5),(35,-8)]):
    a=cyl(f"CandyCanePole_{i:02d}",(x,y,2),0.35,4,WHITE,vertices=16); asset_names.append(a.name)
    b=sphere(f"CandyCaneCap_{i:02d}",(x,y,4.3),0.72,RED,segments=16); asset_names.append(b.name)
for i,(x,y) in enumerate([(-2,-14),(10,-10),(3,11)]):
    g=sphere(f"Gumdrop_{i:02d}",(x,y,0.9),1.25,GREEN,segments=20)
    g.scale.z=0.75
    asset_names.append(g.name)

river_col=cube("COL_River",(18,5,0.1),(5,22,0.6),None,COLLISION,True)
river_col["collision_type"]="hazard"
for i,(x,y) in enumerate(forest):
    o=cyl(f"COL_Lollipop_{i:02d}",(x,y,4),1.0,8,None,COLLISION,vertices=12)
    o["collision_type"]="obstacle"; o.hide_render=True
for i,(x,y) in enumerate(route):
    n=cyl(f"NAV_{i:02d}",(x,y,0.15),0.6,0.3,None,NAV,vertices=12)
    n["nav_index"]=i; n["path_width"]=5.0; n.hide_render=True
spawn=cyl("Spawn_Marker",(-34,-25,0.8),2.0,0.4,RED,GAMEPLAY,vertices=32)
spawn["role"]="player_spawn"

world=bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world=world
world.use_nodes=True
bg=world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value=(0.08,0.05,0.12,1)
    bg.inputs["Strength"].default_value=0.35

bpy.ops.object.light_add(type="SUN",location=(0,0,40))
sun=bpy.context.object
sun.data.energy=2.4
sun.rotation_euler=(math.radians(32),math.radians(-15),math.radians(-35))

bpy.ops.object.light_add(type="AREA",location=(-5,-5,28))
area=bpy.context.object
area.data.energy=1800
area.data.shape="DISK"
area.data.size=40
look_at(area,(0,0,0))

bpy.ops.object.camera_add()
cam=bpy.context.object
cam.data.lens=48
cam.data.clip_end=1000
bpy.context.scene.camera=cam

scene=bpy.context.scene
scene.render.resolution_x=1280
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
try:
    scene.render.engine="BLENDER_EEVEE_NEXT"
except Exception:
    scene.render.engine="BLENDER_EEVEE"

for name,loc,target in [
    ("candyland_iso",(85,-95,72),(0,2,0)),
    ("candyland_spawn_view",(-43,-40,8),(-10,-5,3)),
    ("candyland_castle_view",(52,-5,24),(28,24,5)),
]:
    cam.location=loc
    look_at(cam,target)
    scene.render.filepath=str(OUT/f"{name}.png")
    bpy.ops.render.render(write_still=True)

for o in bpy.context.scene.objects:
    o.select_set(False)
visual=[]
for c in (ENV,PROPS):
    for o in c.objects:
        if o.type=="MESH" and not o.hide_render:
            o.select_set(True)
            visual.append(o)
if visual:
    bpy.context.view_layer.objects.active=visual[0]
    bpy.ops.export_scene.gltf(
        filepath=str(OUT/"candyland_dream_v03.glb"),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
    )

for o in bpy.context.scene.objects:
    o.select_set(False)
props=[bpy.data.objects[n] for n in asset_names if n in bpy.data.objects]
for o in props:
    o.select_set(True)
if props:
    bpy.context.view_layer.objects.active=props[0]
    bpy.ops.export_scene.gltf(
        filepath=str(OUT/"candy_props_v03.glb"),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
    )

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"candyland_dream_v03.blend"))

report={
  "version":"0.3.0",
  "status":"BLENDER_EXECUTED",
  "route_nodes":len(route),
  "path_width_m":5.0,
  "player_clearance_m":1.2,
  "visual_meshes":len(visual),
  "visual_triangles":sum(tri_count(o) for o in visual),
  "procedural_asset_objects":len(props),
  "outputs":[
      "candyland_dream_v03.blend",
      "candyland_dream_v03.glb",
      "candy_props_v03.glb",
      "candyland_iso.png",
      "candyland_spawn_view.png",
      "candyland_castle_view.png",
  ],
}
(OUT/"blender_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
