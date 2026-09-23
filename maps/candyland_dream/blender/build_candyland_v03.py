"""Candyland Dream v0.5 Blender build (v03 compatibility filenames).

Adds recognizable semantic candy props plus verified CC0 GitHub models while
keeping the existing pipeline filenames so downstream validation stays stable.
"""
import bpy, json, math, os, urllib.request, hashlib
from pathlib import Path
from mathutils import Vector

OUT=Path(os.environ.get("CANDY_OUT","candyland/out"))
OUT.mkdir(parents=True,exist_ok=True)
EXT=OUT/"external_cc0"
EXT.mkdir(parents=True,exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def mat(name,color,metallic=0.0,roughness=0.42):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1.0)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF") if m.node_tree else None
    if bsdf:
        bsdf.inputs["Base Color"].default_value=(*color,1.0)
        bsdf.inputs["Roughness"].default_value=roughness
        bsdf.inputs["Metallic"].default_value=metallic
    return m

PINK=mat("Candy_Ground",(0.94,0.40,0.67),roughness=0.6)
PATH=mat("Candy_Path",(0.98,0.65,0.80),roughness=0.5)
CHOCO=mat("Chocolate",(0.20,0.045,0.018),roughness=0.28)
CHOCO2=mat("Milk_Chocolate",(0.42,0.13,0.045),roughness=0.3)
GREEN=mat("Gummy_Green",(0.24,0.86,0.37),roughness=0.32)
MINT=mat("Mint",(0.45,1.0,0.78),roughness=0.3)
RED=mat("Cherry_Red",(1.0,0.08,0.24),roughness=0.28)
CREAM=mat("Vanilla_Cream",(1.0,0.80,0.48),roughness=0.5)
PURPLE=mat("Berry_Purple",(0.60,0.26,0.96),roughness=0.3)
WHITE=mat("Sugar_White",(0.98,0.98,1.0),roughness=0.34)
BLUE=mat("Candy_Blue",(0.30,0.66,1.0),roughness=0.3)
YELLOW=mat("Lemon_Yellow",(1.0,0.86,0.20),roughness=0.32)
ORANGE=mat("Orange_Candy",(1.0,0.40,0.10),roughness=0.3)
BROWN=mat("Gingerbread",(0.58,0.25,0.08),roughness=0.58)
DARK=mat("Dark_Sugar",(0.09,0.04,0.12),roughness=0.5)

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

def add_mat(o,material):
    if o.type=="MESH" and material:
        o.data.materials.clear()
        o.data.materials.append(material)

def cube(name,loc,scale,material=None,c=ENV,hide=False,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    add_mat(o,material); move(o,c); o.hide_render=hide
    return o

def cyl(name,loc,radius,depth,material=None,c=PROPS,vertices=24,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object; o.name=name
    add_mat(o,material); move(o,c)
    return o

def sphere(name,loc,radius,material=None,c=PROPS,segments=24,scale=(1,1,1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=max(8,segments//2),radius=radius,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    add_mat(o,material); move(o,c)
    return o

def cone(name,loc,r1,r2,depth,material=None,c=PROPS,vertices=32,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r1,radius2=r2,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object; o.name=name
    add_mat(o,material); move(o,c)
    return o

def torus(name,loc,major,minor,material=None,c=PROPS,rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=40,minor_segments=12,location=loc,rotation=rot)
    o=bpy.context.object; o.name=name
    add_mat(o,material); move(o,c)
    return o

def join_objects(name,objects,c=PROPS):
    objs=[o for o in objects if o and o.type=="MESH"]
    if not objs: return None
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.object.join()
    out=bpy.context.object; out.name=name; move(out,c)
    return out

def look_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

def tri_count(o):
    if o.type!="MESH": return 0
    o.data.calc_loop_triangles(); return len(o.data.loop_triangles)

def normalize_height(o,target_h):
    bpy.context.view_layer.update()
    h=max(o.dimensions.z,1e-5)
    s=target_h/h
    o.scale=(s,s,s)
    bpy.context.view_layer.update()
    minz=min((o.matrix_world @ Vector(c)).z for c in o.bound_box)
    o.location.z-=minz
    return o

def download(url,path):
    if not path.exists() or path.stat().st_size<100:
        with urllib.request.urlopen(url,timeout=30) as r:
            path.write_bytes(r.read())
    return hashlib.sha256(path.read_bytes()).hexdigest()

def import_fbx_cc0(name,url,loc,target_h,material,collection=PROPS,rotation_z=0.0):
    path=EXT/(name+".fbx")
    digest=download(url,path)
    before=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path))
    new=[o for o in bpy.data.objects if o not in before]
    meshes=[o for o in new if o.type=="MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh imported from {url}")
    for o in new:
        if o.type!="MESH": bpy.data.objects.remove(o,do_unlink=True)
    obj=join_objects(name,meshes,collection)
    add_mat(obj,material)
    obj.rotation_euler.z=rotation_z
    normalize_height(obj,target_h)
    obj.location.x=loc[0]; obj.location.y=loc[1]
    obj["source_license"]="CC0-1.0"
    obj["source_url"]=url
    obj["source_sha256"]=digest
    return obj,{"name":name,"url":url,"sha256":digest,"license":"CC0-1.0"}

def make_cupcake_house(name,loc,scale=1.0):
    x,y=loc; parts=[]
    parts.append(cyl(name+"_Wrapper",(x,y,1.7*scale),2.6*scale,3.4*scale,PURPLE,vertices=32))
    parts.append(sphere(name+"_Frosting",(x,y,3.9*scale),2.55*scale,WHITE,segments=32,scale=(1,1,0.62)))
    parts.append(sphere(name+"_Cherry",(x,y,5.45*scale),0.58*scale,RED,segments=20))
    parts.append(cube(name+"_Door",(x,y-2.55*scale,1.35*scale),(0.75*scale,0.18*scale,1.25*scale),CHOCO2,PROPS))
    for sx in (-1,1):
        parts.append(sphere(name+f"_Window_{sx}",(x+1.25*sx*scale,y-2.45*scale,2.45*scale),0.48*scale,BLUE,segments=16,scale=(1,0.25,1)))
    return join_objects(name,parts)

def make_icecream_tower(name,loc,scale=1.0):
    x,y=loc; parts=[]
    parts.append(cone(name+"_Cone",(x,y,2.6*scale),2.15*scale,0.65*scale,5.2*scale,CREAM,vertices=40))
    for i,(matr,dx,dy) in enumerate([(PINK,-0.55,0),(MINT,0.55,0),(PURPLE,0,0.45)]):
        parts.append(sphere(name+f"_Scoop_{i}",(x+dx*scale,y+dy*scale,5.45*scale),1.55*scale,matr,segments=28))
    parts.append(sphere(name+"_Cherry",(x,y,7.15*scale),0.42*scale,RED,segments=18))
    return join_objects(name,parts)

def make_donut_arch(name,loc,scale=1.0):
    x,y=loc; parts=[]
    parts.append(cyl(name+"_PillarL",(x-3*scale,y,2.2*scale),0.75*scale,4.4*scale,CHOCO2,vertices=24))
    parts.append(cyl(name+"_PillarR",(x+3*scale,y,2.2*scale),0.75*scale,4.4*scale,CHOCO2,vertices=24))
    parts.append(torus(name+"_Donut",(x,y,5.1*scale),3.15*scale,0.95*scale,PINK,rot=(math.radians(90),0,0)))
    for a,matr in [(0,WHITE),(0.7,YELLOW),(1.4,BLUE),(2.1,GREEN),(2.8,RED)]:
        sx=x+math.cos(a)*2.8*scale; sz=5.1*scale+math.sin(a)*2.8*scale
        parts.append(cyl(name+f"_Sprinkle_{a:.1f}",(sx,y-0.95*scale,sz),0.10*scale,0.70*scale,matr,vertices=10,rot=(0,math.radians(90),a)))
    return join_objects(name,parts)

def make_gingerbread_shop(name,loc,scale=1.0):
    x,y=loc; parts=[]
    parts.append(cube(name+"_Body",(x,y,2.1*scale),(3.4*scale,2.8*scale,2.1*scale),BROWN,PROPS))
    parts.append(cube(name+"_RoofA",(x-1.7*scale,y,4.7*scale),(2.55*scale,3.05*scale,0.35*scale),RED,PROPS,rot=(0,math.radians(35),0)))
    parts.append(cube(name+"_RoofB",(x+1.7*scale,y,4.7*scale),(2.55*scale,3.05*scale,0.35*scale),WHITE,PROPS,rot=(0,math.radians(-35),0)))
    parts.append(cube(name+"_Door",(x,y-2.85*scale,1.45*scale),(0.8*scale,0.18*scale,1.45*scale),CHOCO,PROPS))
    for sx in (-1,1): parts.append(sphere(name+f"_Window_{sx}",(x+1.8*sx*scale,y-2.75*scale,2.7*scale),0.62*scale,BLUE,segments=16,scale=(1,0.2,1)))
    for sx in (-1,1): parts.append(cyl(name+f"_CandyPost_{sx}",(x+3.0*sx*scale,y-2.7*scale,1.5*scale),0.22*scale,3.0*scale,WHITE,vertices=14))
    return join_objects(name,parts)

def make_gummy_bear(name,loc,scale=1.0,material=GREEN):
    x,y=loc; parts=[]
    parts.append(sphere(name+"_Body",(x,y,1.8*scale),1.35*scale,material,segments=24,scale=(0.9,0.65,1.15)))
    parts.append(sphere(name+"_Head",(x,y,3.25*scale),1.0*scale,material,segments=24))
    for sx in (-1,1):
        parts.append(sphere(name+f"_Ear_{sx}",(x+0.72*sx*scale,y,4.0*scale),0.42*scale,material,segments=16))
        parts.append(cyl(name+f"_Arm_{sx}",(x+1.3*sx*scale,y,2.1*scale),0.38*scale,1.45*scale,material,vertices=16,rot=(0,math.radians(25*sx),0)))
        parts.append(cyl(name+f"_Leg_{sx}",(x+0.62*sx*scale,y,0.65*scale),0.44*scale,1.3*scale,material,vertices=16))
    return join_objects(name,parts)

def make_chocolate_fountain(name,loc,scale=1.0):
    x,y=loc; parts=[]
    parts.append(cyl(name+"_Basin",(x,y,0.45*scale),3.2*scale,0.9*scale,CHOCO2,vertices=40))
    parts.append(cyl(name+"_Column",(x,y,2.5*scale),0.65*scale,4.2*scale,CHOCO,vertices=28))
    for i,(z,r) in enumerate([(1.6,2.5),(2.9,1.8),(4.1,1.15)]): parts.append(cone(name+f"_Tier_{i}",(x,y,z*scale),r*scale,0.35*scale,0.55*scale,CHOCO2,vertices=36))
    parts.append(sphere(name+"_Top",(x,y,4.85*scale),0.55*scale,CHOCO,segments=20))
    return join_objects(name,parts)

def make_candy_cart(name,loc,scale=1.0):
    x,y=loc; parts=[]
    parts.append(cube(name+"_Box",(x,y,1.8*scale),(2.5*scale,1.6*scale,1.1*scale),PINK,PROPS))
    parts.append(cube(name+"_Awning",(x,y,3.55*scale),(2.85*scale,1.9*scale,0.22*scale),WHITE,PROPS))
    for sx in (-1,1):
        parts.append(torus(name+f"_Wheel_{sx}",(x+2.15*sx*scale,y,0.75*scale),0.82*scale,0.22*scale,CHOCO,rot=(math.radians(90),0,0)))
    for sx in (-1,1): parts.append(cyl(name+f"_Post_{sx}",(x+2.2*sx*scale,y,2.8*scale),0.13*scale,3.4*scale,RED,vertices=12))
    return join_objects(name,parts)

cube("Candyland_Ground",(0,0,-1),(48,36,1),PINK)
route=[(-34,-25),(-25,-20),(-12,-10),(-20,3),(-28,18),(0,-2),(18,5),(28,24)]
for i,(x,y) in enumerate(route):
    parts=[cyl(f"CookiePath_{i:02d}_Base",(x,y,0.28),3.15,0.56,BROWN,ENV,vertices=36)]
    for j,a in enumerate((0.25,1.35,2.45,3.55,4.65,5.55)):
        px=x+math.cos(a)*1.75; py=y+math.sin(a)*1.55
        parts.append(cyl(f"CookiePath_{i:02d}_Chip_{j}",(px,py,0.60),0.25,0.12,CHOCO,ENV,vertices=12))
    cookie=join_objects(f"CookiePath_{i:02d}",parts,ENV)
    cookie.rotation_euler.z=math.radians((-1)**i*6)

cyl("Candy_Plaza",(-12,-10,0.2),8,0.5,CREAM,ENV,vertices=48)
make_chocolate_fountain("Chocolate_Fountain",(-12,-10),0.9)

cube("Chocolate_River",(18,5,-0.25),(5,22,0.25),CHOCO,ENV)
for i,y in enumerate([-12,-4,4,12,20]):
    m=cyl(f"Marshmallow_Step_{i:02d}",(18,y,0.4),1.7,0.7,WHITE,ENV,vertices=28)
    m.rotation_euler.z=math.radians(i*11)

cc0=[]
external_specs=[
    ("CottonCandyTree_A","https://raw.githubusercontent.com/SkywolfGameStudios/CC0Tree/main/Assets/SM_Tree_Rounded.fbx",(-38,10),9.0,PINK,0.0),
    ("CottonCandyTree_B","https://raw.githubusercontent.com/SkywolfGameStudios/CC0Tree/main/Assets/SM_Tree_Rounded.fbx",(-22,12),7.5,BLUE,0.7),
    ("MintPine_A","https://raw.githubusercontent.com/SkywolfGameStudios/CC0Tree/main/Assets/SM_Pine_Tree.fbx",(-31,27),10.0,MINT,0.2),
    ("MintPine_B","https://raw.githubusercontent.com/SkywolfGameStudios/CC0Tree/main/Assets/SM_Pine_Tree.fbx",(-40,28),8.0,WHITE,-0.5),
    ("SyrupWateringCan","https://raw.githubusercontent.com/SkywolfGameStudios/CC0Tree/main/Assets/SM_WateringCan.fbx",(8,-18),3.2,PURPLE,0.4),
    ("CandyBin","https://raw.githubusercontent.com/SkywolfGameStudios/CC0Tree/main/Assets/SM_TrashCan.fbx",(-3,-7),2.8,BLUE,-0.2),
    ("CandyBench","https://raw.githubusercontent.com/KayKit-Game-Assets/KayKit-Halloween-Bits-1.0/main/addons/kaykit_halloween_bits/Assets/fbx/bench.fbx",(-11,9),2.2,PINK,-0.35),
    ("CookieCrate","https://raw.githubusercontent.com/KayKit-Game-Assets/KayKit-Restaurant-Bits-1.0/main/addons/kaykit_restaurant_bits/Assets/fbx/crate_buns.fbx",(13,-15),2.6,CREAM,0.30),
]
for spec in external_specs:
    obj,meta=import_fbx_cc0(spec[0],spec[1],spec[2],spec[3],spec[4],PROPS,spec[5]); cc0.append(meta)

semantic=[]
semantic += [make_cupcake_house("Cupcake_House_A",(-17,22),0.9), make_cupcake_house("Cupcake_House_B",(-3,22),0.72)]
semantic += [make_icecream_tower("IceCream_Tower_A",(2,13),0.9), make_icecream_tower("IceCream_Tower_B",(9,20),0.7)]
semantic += [make_donut_arch("Donut_Gate",(-25,-15),0.95)]
semantic += [make_gingerbread_shop("Gingerbread_Shop",(-6,-18),0.9)]
semantic += [make_gummy_bear("Gummy_Bear_Green",(5,-9),0.85,GREEN), make_gummy_bear("Gummy_Bear_Red",(10,-3),0.65,RED)]
semantic += [make_candy_cart("Candy_Cart",(-28,-3),0.8)]

cyl("Castle_Platform",(28,24,0.5),12,1.0,CREAM,ENV,vertices=48)
castle_parts=[
    cube("Castle_MainHall",(28,24,4.0),(5.5,4.4,3.0),CREAM,PROPS),
    cube("Castle_IcingBand",(28,19.45,5.8),(5.8,0.38,0.38),WHITE,PROPS),
    cube("Castle_Entrance",(28,19.2,2.3),(1.35,0.55,2.25),DARK,PROPS),
]
for sx in (-4.6,-2.3,0,2.3,4.6):
    castle_parts.append(cube(f"Castle_SugarBattlement_{sx}",(28+sx,19.4,7.25),(0.55,0.55,0.55),WHITE,PROPS))
for i,(dx,dy,r,h) in enumerate([(-6,-5,2.2,8),(6,-5,2.2,8),(-6,5,2.4,10),(6,5,2.4,10),(0,0,3.2,14)]):
    tower=cyl(f"CastleTower_{i:02d}",(28+dx,24+dy,h/2+1),r,h,PURPLE,PROPS,vertices=32); castle_parts.append(tower)
    roof=cone(f"CastleRoof_{i:02d}",(28+dx,24+dy,h+2.4),r*1.25,0.15,4.6,RED,PROPS,vertices=32); castle_parts.append(roof)
    pearl=sphere(f"CastlePearl_{i:02d}",(28+dx,24+dy,h+4.8),0.42,WHITE,PROPS,segments=18); castle_parts.append(pearl)
for x in (23,28,33):
    for z in (3.0,6.0):
        castle_parts.append(sphere(f"CastleWindow_{x}_{z}",(x,18.2,z),0.52,BLUE,PROPS,segments=16,scale=(1,0.18,1)))
castle=join_objects("Candy_Castle",castle_parts,PROPS)

gate=cube("Castle_Gate_Blocker",(28,13,2.5),(4,0.5,2.5),CREAM,GAMEPLAY)
gate["role"]="toggle_gate"; gate["default_locked"]=True

for i,(x,y) in enumerate([(-5,8),(8,18),(5,-20),(-35,-5),(35,-8),(-14,8)]):
    pole=cyl(f"CandyLamp_{i}_Pole",(x,y,2.0),0.28,4.0,WHITE,PROPS,vertices=16)
    globe=sphere(f"CandyLamp_{i}_Globe",(x,y,4.45),0.72,RED if i%2==0 else BLUE,PROPS,segments=20)
    ring=torus(f"CandyLamp_{i}_Ring",(x,y,3.65),0.48,0.10,YELLOW,PROPS)
    semantic.append(join_objects(f"Candy_Lamp_{i:02d}",[pole,globe,ring],PROPS))

for i,(x,y,matr) in enumerate([(-2,-14,GREEN),(10,-10,RED),(3,11,PURPLE),(14,16,YELLOW)]):
    g=sphere(f"Gumdrop_{i:02d}",(x,y,0.9),1.25,matr,PROPS,segments=24,scale=(1,1,0.75)); semantic.append(g)

river_col=cube("COL_River",(18,5,0.1),(5,22,0.6),None,COLLISION,True); river_col["collision_type"]="hazard"
for i,(x,y) in enumerate([(-38,10),(-22,12),(-31,27),(-40,28),(-17,22),(-3,22),(2,13),(9,20)]):
    o=cyl(f"COL_Prop_{i:02d}",(x,y,3),1.6,6,None,COLLISION,vertices=12); o["collision_type"]="obstacle"; o.hide_render=True
for i,(x,y) in enumerate(route):
    n=cyl(f"NAV_{i:02d}",(x,y,0.15),0.6,0.3,None,NAV,vertices=12); n["nav_index"]=i; n["path_width"]=5.0; n.hide_render=True
spawn=cyl("Spawn_Marker",(-34,-25,0.8),2.0,0.4,RED,GAMEPLAY,vertices=32); spawn["role"]="player_spawn"

world=bpy.context.scene.world or bpy.data.worlds.new("World"); bpy.context.scene.world=world; world.use_nodes=True
bg=world.node_tree.nodes.get("Background")
if bg: bg.inputs["Color"].default_value=(0.045,0.025,0.075,1); bg.inputs["Strength"].default_value=0.28
bpy.ops.object.light_add(type="SUN",location=(0,0,40)); sun=bpy.context.object; sun.data.energy=2.6; sun.rotation_euler=(math.radians(30),math.radians(-18),math.radians(-35))
bpy.ops.object.light_add(type="AREA",location=(-4,-8,30)); area=bpy.context.object; area.data.energy=2100; area.data.shape="DISK"; area.data.size=42; look_at(area,(0,2,0))
bpy.ops.object.light_add(type="AREA",location=(38,32,18)); fill=bpy.context.object; fill.data.energy=900; fill.data.size=24; look_at(fill,(22,20,4))

bpy.ops.object.camera_add(); cam=bpy.context.object; cam.data.lens=48; cam.data.clip_end=1000; bpy.context.scene.camera=cam
scene=bpy.context.scene; scene.render.resolution_x=1280; scene.render.resolution_y=720; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"
try: scene.render.engine="BLENDER_EEVEE_NEXT"
except Exception: scene.render.engine="BLENDER_EEVEE"

for name,loc,target in [
    ("candyland_iso",(88,-100,76),(0,2,3)),
    ("candyland_spawn_view",(-45,-43,11),(-13,-7,3.5)),
    ("candyland_castle_view",(55,-2,27),(28,24,6.5)),
]:
    cam.location=loc; look_at(cam,target); scene.render.filepath=str(OUT/f"{name}.png"); bpy.ops.render.render(write_still=True)

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
report={
  "version":"0.5.0",
  "status":"BLENDER_EXECUTED",
  "compatibility_filenames":"v03",
  "route_nodes":len(route),"path_width_m":5.0,"player_clearance_m":1.2,
  "visual_meshes":len(visual),"visual_triangles":sum(tri_count(o) for o in visual),
  "procedural_asset_objects":len(props),"external_cc0_assets":cc0,
  "outputs":["candyland_dream_v03.blend","candyland_dream_v03.glb","candy_props_v03.glb","candyland_iso.png","candyland_spawn_view.png","candyland_castle_view.png"]
}
(OUT/"blender_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
