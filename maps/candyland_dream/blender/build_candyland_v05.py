"""Candyland Dream v0.5 Vision Pass.

Builds on the verified v0.5-compatible base generator, then adds a richer
environment/art-direction pass while preserving downstream compatibility names.
"""
from pathlib import Path
import bpy, json, math, random

# Execute the verified base world first. It leaves its helper functions,
# materials, collections, OUT path, scene and camera available in globals().
BASE=Path(__file__).with_name("build_candyland_v03.py")
exec(compile(BASE.read_text(encoding="utf-8"), str(BASE), "exec"), globals())

random.seed(5051993)

# ---------- extra v0.5 materials ----------
GOLD = mat("Caramel_Gold",(1.0,0.44,0.06),metallic=0.12,roughness=0.27)
CYAN = mat("Magic_Cyan",(0.08,0.82,1.0),roughness=0.22)
MAGENTA = mat("Magic_Magenta",(1.0,0.06,0.55),roughness=0.22)
LIME = mat("Magic_Lime",(0.48,1.0,0.18),roughness=0.24)
COOKIE = mat("Wafer_Biscuit",(0.82,0.50,0.20),roughness=0.64)
FROST = mat("Frosting_Cloud",(1.0,0.84,0.94),roughness=0.46)

# Give the magic candies a subtle emissive quality.
for m in (CYAN,MAGENTA,LIME):
    if m.use_nodes:
        bsdf=m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value=m.diffuse_color
                bsdf.inputs["Emission Strength"].default_value=1.8
            elif "Emission" in bsdf.inputs:
                bsdf.inputs["Emission"].default_value=m.diffuse_color

# ---------- new modular builders ----------
def make_lollipop(name,loc,height=6.0,r=1.25,head_mat=PINK):
    x,y=loc
    pieces=[
        cyl(name+"_Stick",(x,y,height*0.47),0.15,height*0.94,WHITE,PROPS,vertices=16),
        sphere(name+"_Head",(x,y,height),r,head_mat,PROPS,segments=28,scale=(1.0,0.36,1.0)),
        torus(name+"_Rim",(x,y-0.04,height),r*0.72,0.11,WHITE,PROPS,rot=(math.radians(90),0,0)),
    ]
    return join_objects(name,pieces,PROPS)

def make_candy_cane(name,loc,height=6.0,scale=1.0,mat_a=WHITE,mat_b=RED):
    x,y=loc
    parts=[]
    parts.append(cyl(name+"_Stem",(x,y,height*0.42),0.23*scale,height*0.84,mat_a,PROPS,vertices=18))
    # stripes as visible rings
    for i in range(6):
        parts.append(torus(name+f"_Stripe_{i}",(x,y,0.8+i*0.7),0.25*scale,0.075*scale,mat_b,PROPS))
    # hook made from small candy beads
    for i,a in enumerate([0.15,0.48,0.82,1.15,1.48,1.80,2.10]):
        px=x+math.sin(a)*1.10*scale
        pz=height-0.15+math.cos(a)*1.10*scale
        parts.append(sphere(name+f"_Hook_{i}",(px,y,pz),0.28*scale,mat_a if i%2==0 else mat_b,PROPS,segments=14))
    return join_objects(name,parts,PROPS)

def make_star_candy(name,loc,scale=1.0,material=GOLD):
    # stylized faceted magical candy / crystal
    x,y,z=loc
    parts=[
        sphere(name+"_Core",(x,y,z),0.72*scale,material,PROPS,segments=16,scale=(1,0.6,1)),
        cone(name+"_Top",(x,y,z+1.05*scale),0.55*scale,0.02,1.4*scale,material,PROPS,vertices=6),
        cone(name+"_Bottom",(x,y,z-1.05*scale),0.55*scale,0.02,1.4*scale,material,PROPS,vertices=6,rot=(math.pi,0,0)),
    ]
    return join_objects(name,parts,PROPS)

def make_market_stall(name,loc,scale=1.0,accent=PINK):
    x,y=loc
    parts=[
        cube(name+"_Counter",(x,y,1.25*scale),(2.2*scale,1.2*scale,1.15*scale),COOKIE,PROPS),
        cube(name+"_Awning",(x,y,3.35*scale),(2.65*scale,1.55*scale,0.25*scale),accent,PROPS),
    ]
    for sx in (-1,1):
        parts.append(cyl(name+f"_Post_{sx}",(x+2.2*sx*scale,y,2.25*scale),0.12*scale,3.9*scale,WHITE,PROPS,vertices=12))
    for i in range(5):
        px=x-1.5*scale+i*.75*scale
        parts.append(sphere(name+f"_Candy_{i}",(px,y-1.0*scale,2.15*scale),0.32*scale,
                            (CYAN,MAGENTA,LIME,YELLOW,PURPLE)[i],PROPS,segments=14))
    return join_objects(name,parts,PROPS)

def make_wafer_bridge(name,center=(18,5),length=11,width=8):
    cx,cy=center
    parts=[]
    # deck crosses the river in X direction
    for i in range(length):
        x=cx-width/2 + i*(width/(length-1))
        parts.append(cube(name+f"_Plank_{i}",(x,cy,1.05),(0.34,2.5,0.23),COOKIE,ENV))
        # chocolate seam
        parts.append(cube(name+f"_Choc_{i}",(x,cy-2.18,1.18),(0.25,0.08,0.11),CHOCO,ENV))
    for side in (-1,1):
        parts.append(cyl(name+f"_Rail_{side}",(cx,cy+side*2.65,2.05),0.13,width,WHITE,ENV,vertices=14,rot=(0,math.radians(90),0)))
        for i in range(5):
            x=cx-width/2+i*width/4
            parts.append(cyl(name+f"_RailPost_{side}_{i}",(x,cy+side*2.65,1.65),0.12,1.5,RED if i%2 else WHITE,ENV,vertices=12))
    return join_objects(name,parts,ENV)

def make_frosting_cliff(name,loc,scale=(6,4,3),material=FROST):
    x,y=loc
    pieces=[
        sphere(name+"_A",(x,y,-0.2),1.0,material,ENV,segments=20,scale=scale),
        sphere(name+"_B",(x+scale[0]*0.65,y+scale[1]*0.25,0.15),1.0,material,ENV,segments=20,scale=(scale[0]*.65,scale[1]*.7,scale[2]*.75)),
        sphere(name+"_C",(x-scale[0]*0.60,y-scale[1]*0.18,0.10),1.0,material,ENV,segments=20,scale=(scale[0]*.55,scale[1]*.75,scale[2]*.70)),
    ]
    return join_objects(name,pieces,ENV)

# ---------- Spawn: unmistakable candy gateway ----------
spawn_gateway=[]
for sx in (-1,1):
    spawn_gateway.append(make_candy_cane(f"Spawn_Cane_{sx}",(-34+sx*3.6,-22.5),6.8,1.15,WHITE,RED if sx<0 else BLUE))
spawn_gateway += [
    cube("Spawn_Sign_Board",(-34,-22.5,6.55),(3.7,0.35,0.9),PURPLE,PROPS),
    sphere("Spawn_Sign_Gem",(-34,-22.05,7.85),0.45,CYAN,PROPS,segments=16),
]
spawn_gateway=join_objects("Candyland_Spawn_Gateway",[o for o in spawn_gateway if o],PROPS)

# ---------- Candy Plaza: market density ----------
for i,(x,y,accent) in enumerate([
    (-19,-15,PINK),(-14,-17,BLUE),(-8,-16,YELLOW),(-4,-12,MINT)
]):
    make_market_stall(f"Candy_Market_{i}",(x,y),0.68,accent)

# giant donut seating around plaza
for i,a in enumerate([0.4,1.7,2.9,4.1,5.2]):
    x=-12+math.cos(a)*10.5
    y=-10+math.sin(a)*8.4
    d=torus(f"Donut_Seat_{i}",(x,y,0.9),1.15,0.40,(PINK,BLUE,YELLOW,PURPLE,MINT)[i],PROPS,rot=(math.radians(90),0,a))
    # cookie base
    cyl(f"Donut_Seat_Base_{i}",(x,y,0.28),1.30,0.45,COOKIE,PROPS,vertices=28)

# ---------- Lollipop Forest: actual forest ----------
forest_heads=[PINK,PURPLE,BLUE,MINT,YELLOW,RED,MAGENTA,CYAN]
forest_positions=[
    (-42,8),(-37,14),(-31,11),(-25,15),(-20,18),(-39,21),(-33,24),(-25,25),
    (-18,28),(-43,29),(-35,32),(-27,33),(-20,35),(-15,30),(-11,24),(-46,18)
]
for i,(x,y) in enumerate(forest_positions):
    make_lollipop(f"Lollipop_Forest_{i:02d}",(x,y),height=5.0+(i%5)*0.7,r=0.9+(i%4)*0.16,head_mat=forest_heads[i%len(forest_heads)])

# gummy stepping stones / mushrooms
for i,(x,y) in enumerate([(-33,16),(-28,20),(-22,22),(-38,27),(-17,25),(-12,29)]):
    sphere(f"Gummy_Mushroom_Cap_{i}",(x,y,1.8),1.25,(RED,PURPLE,BLUE,MINT,YELLOW,MAGENTA)[i],PROPS,segments=20,scale=(1.25,1.0,0.48))
    cyl(f"Gummy_Mushroom_Stem_{i}",(x,y,0.9),0.38,1.8,WHITE,PROPS,vertices=18)

# ---------- Chocolate River: hero bridge + banks ----------
make_wafer_bridge("Grand_Wafer_Bridge",(18,5),12,10)
for y in (-14,-7,0,7,14,21):
    # marshmallow banks
    sphere(f"River_Bank_L_{y}",(12.1,y,0.1),2.25,WHITE,ENV,segments=20,scale=(1.1,1.7,.6))
    sphere(f"River_Bank_R_{y}",(23.9,y,0.1),2.25,FROST,ENV,segments=20,scale=(1.1,1.7,.6))

# ---------- Castle approach: fantasy candy avenue ----------
for i,y in enumerate([12,15.5,19]):
    make_star_candy(f"Castle_Crystal_L_{i}",(23.0,y,2.0),0.78,(CYAN,MAGENTA,LIME)[i])
    make_star_candy(f"Castle_Crystal_R_{i}",(33.0,y,2.0),0.78,(MAGENTA,LIME,CYAN)[i])

for i,(x,y) in enumerate([(21,22),(35,22),(22,29),(34,30)]):
    make_cupcake_house(f"Castle_Village_Cupcake_{i}",(x,y),0.48+(i%2)*0.08)

# ---------- Frosting cliffs frame the map edges ----------
cliffs=[
    ("Cliff_SW",(-47,-31),(7,5,2.7),FROST),
    ("Cliff_W",(-49,-3),(6,8,3.4),WHITE),
    ("Cliff_NW",(-43,34),(8,5,3.0),FROST),
    ("Cliff_N",(2,38),(12,4,2.5),WHITE),
    ("Cliff_NE",(43,33),(7,5,3.3),FROST),
    ("Cliff_E",(48,6),(5,10,3.5),WHITE),
    ("Cliff_SE",(41,-30),(8,5,2.8),FROST),
]
for n,loc,sc,ma in cliffs:
    make_frosting_cliff(n,loc,sc,ma)

# ---------- Sprinkle fields: small, cheap visual detail ----------
sprinkle_mats=[RED,BLUE,YELLOW,MINT,PURPLE,MAGENTA,CYAN]
for i in range(70):
    x=random.uniform(-44,44); y=random.uniform(-32,34)
    # keep main route a little clearer
    if abs(x-18)<6 and -18<y<25: 
        continue
    r=random.uniform(.08,.17)
    o=cyl(f"Ground_Sprinkle_{i:02d}",(x,y,0.23),r,random.uniform(.45,.85),sprinkle_mats[i%len(sprinkle_mats)],ENV,vertices=8,
          rot=(random.uniform(-.3,.3),random.uniform(-.3,.3),random.uniform(0,math.tau)))
    o.scale.z=.28
    o["catalog_skip"]=True

# ---------- polish lighting ----------
bpy.ops.object.light_add(type="POINT",location=(-12,-10,7))
plaza_light=bpy.context.object; plaza_light.name="Plaza_Magic_Light"; plaza_light.data.energy=850; plaza_light.data.color=(1.0,.25,.58); plaza_light.data.shadow_soft_size=5
bpy.ops.object.light_add(type="POINT",location=(28,24,12))
castle_light=bpy.context.object; castle_light.name="Castle_Magic_Light"; castle_light.data.energy=1200; castle_light.data.color=(.22,.52,1.0); castle_light.data.shadow_soft_size=6
bpy.ops.object.light_add(type="POINT",location=(-29,23,9))
forest_light=bpy.context.object; forest_light.name="Forest_Magic_Light"; forest_light.data.energy=900; forest_light.data.color=(.35,1.0,.55); forest_light.data.shadow_soft_size=5

# ---------- v0.5 hero renders ----------
scene=bpy.context.scene
scene.render.resolution_x=1280
scene.render.resolution_y=720
try:
    scene.view_settings.look='AgX - Medium High Contrast'
except Exception:
    pass

shots=[
    ("candyland_iso",(92,-104,80),(0,3,4)),
    ("candyland_spawn_view",(-49,-46,13),(-20,-8,4)),
    ("candyland_castle_view",(58,-1,30),(28,24,7)),
    ("candyland_plaza_view",(-34,-34,18),(-12,-10,3)),
    ("candyland_forest_view",(-58,2,18),(-29,23,4.5)),
    ("candyland_river_view",(43,-20,18),(18,5,2.5)),
]
if os.environ.get("CANDY_DEFER_INTERMEDIATE_RENDERS","0")!="1":
    for name,loc,target in shots:
        cam.location=loc
        look_at(cam,target)
        scene.render.filepath=str(OUT/f"{name}.png")
        bpy.ops.render.render(write_still=True)

# ---------- overwrite compatibility exports with enriched v0.5 ----------
for o in bpy.context.scene.objects:
    o.select_set(False)
visual=[]
for c in (ENV,PROPS):
    for o in c.objects:
        if o.type=="MESH" and not o.hide_render:
            o.select_set(True); visual.append(o)
if visual:
    bpy.context.view_layer.objects.active=visual[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT/"candyland_dream_v03.glb"),export_format="GLB",use_selection=True,export_apply=True)

for o in bpy.context.scene.objects:
    o.select_set(False)
props=[o for o in PROPS.objects if o.type=="MESH" and not o.hide_render]
for o in props:
    o.select_set(True)
if props:
    bpy.context.view_layer.objects.active=props[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT/"candy_props_v03.glb"),export_format="GLB",use_selection=True,export_apply=True)

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"candyland_dream_v03.blend"))

# Merge base report with vision-pass facts.
report_path=OUT/"blender_report.json"
report=json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
report.update({
    "version":"0.5.1",
    "status":"BLENDER_EXECUTED",
    "vision_pass":"MAGICAL_DETAIL_PASS",
    "visual_meshes":len(visual),
    "visual_triangles":sum(tri_count(o) for o in visual),
    "procedural_asset_objects":len(props),
    "new_v05_features":[
        "spawn_candy_gateway","candy_market","dense_lollipop_forest",
        "grand_wafer_bridge","river_marshmallow_banks","castle_crystal_avenue",
        "castle_village_cupcakes","frosting_cliffs","ground_sprinkles","magic_lighting"
    ],
    "beauty_renders":[x[0]+".png" for x in shots],
})
report_path.write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
