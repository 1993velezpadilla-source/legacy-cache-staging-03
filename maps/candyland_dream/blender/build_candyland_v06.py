"""Candyland Dream v0.6 Gloss & Girly Map Pass.

Executes the verified v0.5 world, then applies a real Blender art-direction pass:
- controlled glossy feminine palette
- procedural candy / frosting / iridescent materials
- continuous glossy route ribbons
- premium heart, bow, crystal, gold and cherry decorations
- map-wide material remapping
- dreamy lighting + compositor glow
- compatibility GLB/BLEND exports and QA report
"""
from pathlib import Path
import bpy, json, math

BASE=Path(__file__).with_name("build_candyland_v05.py")
exec(compile(BASE.read_text(encoding="utf-8"), str(BASE), "exec"), globals())

# ---------------------------------------------------------------------------
# Palette locked from the approved glossy/girly concept direction.
# ---------------------------------------------------------------------------
PALETTE={
    "cherry_red": (0.82,0.015,0.12),
    "hot_pink": (1.00,0.075,0.42),
    "bubblegum": (1.00,0.28,0.62),
    "blush": (1.00,0.63,0.76),
    "cream": (1.00,0.90,0.86),
    "pearl": (1.00,0.95,0.98),
    "lavender": (0.72,0.48,1.00),
    "candy_cyan": (0.34,0.88,1.00),
    "mint": (0.54,1.00,0.80),
    "peach": (1.00,0.58,0.40),
    "gold": (1.00,0.52,0.075),
    "chocolate": (0.22,0.035,0.018),
    "milk_chocolate": (0.47,0.13,0.055),
}

def new_principled(name,base,rough=.2,metallic=0.0,coat=0.7,emission=None,emission_strength=0.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*base,1)
    m.use_nodes=True
    nt=m.node_tree
    nt.nodes.clear()
    out=nt.nodes.new("ShaderNodeOutputMaterial")
    bs=nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value=(*base,1)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metallic
    if "Coat Weight" in bs.inputs: bs.inputs["Coat Weight"].default_value=coat
    if "Coat Roughness" in bs.inputs: bs.inputs["Coat Roughness"].default_value=max(.03,rough*.45)
    if "Clearcoat" in bs.inputs: bs.inputs["Clearcoat"].default_value=coat
    if "Clearcoat Roughness" in bs.inputs: bs.inputs["Clearcoat Roughness"].default_value=max(.03,rough*.45)
    if emission:
        if "Emission Color" in bs.inputs:
            bs.inputs["Emission Color"].default_value=(*emission,1)
            bs.inputs["Emission Strength"].default_value=emission_strength
        elif "Emission" in bs.inputs:
            bs.inputs["Emission"].default_value=(*emission,1)
    nt.links.new(bs.outputs["BSDF"],out.inputs["Surface"])
    return m

def frosting_mat(name,base):
    m=new_principled(name,base,rough=.34,coat=.38)
    nt=m.node_tree; bs=nt.nodes.get("Principled BSDF")
    noise=nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value=4.5; noise.inputs["Detail"].default_value=3.0; noise.inputs["Roughness"].default_value=.55
    bump=nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value=.11; bump.inputs["Distance"].default_value=.12
    nt.links.new(noise.outputs["Fac"],bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"],bs.inputs["Normal"])
    return m

def iridescent_mat(name):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(1.0,.55,.78,1)
    m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new("ShaderNodeOutputMaterial")
    bs=nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Roughness"].default_value=.13
    bs.inputs["Metallic"].default_value=.10
    if "Coat Weight" in bs.inputs: bs.inputs["Coat Weight"].default_value=1.0
    if "Coat Roughness" in bs.inputs: bs.inputs["Coat Roughness"].default_value=.05
    layer=nt.nodes.new("ShaderNodeLayerWeight")
    ramp=nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    e0=ramp.color_ramp.elements[0]; e0.position=0.0; e0.color=(1.0,.34,.68,1)
    e1=ramp.color_ramp.elements.new(.33); e1.color=(.48,.68,1.0,1)
    e2=ramp.color_ramp.elements.new(.66); e2.color=(.54,1.0,.82,1)
    e3=ramp.color_ramp.elements.new(.86); e3.color=(.80,.56,1.0,1)
    e4=ramp.color_ramp.elements.new(1.0); e4.color=(1.0,.86,.96,1)
    nt.links.new(layer.outputs["Facing"],ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"],bs.inputs["Base Color"])
    nt.links.new(bs.outputs["BSDF"],out.inputs["Surface"])
    return m

BUBBLEGUM_GLOSS=new_principled("V06_Bubblegum_Gloss",PALETTE["bubblegum"],rough=.12,coat=1.0)
HOT_PINK_GLOSS=new_principled("V06_Hot_Pink_Gloss",PALETTE["hot_pink"],rough=.10,coat=1.0)
CHERRY_GLOSS=new_principled("V06_Cherry_Candy_Shell",PALETTE["cherry_red"],rough=.09,coat=1.0)
BLUSH_GLOSS=new_principled("V06_Blush_Gloss",PALETTE["blush"],rough=.18,coat=.9)
PEARL_FROST=frosting_mat("V06_Pearl_Frosting",PALETTE["pearl"])
CREAM_FROST=frosting_mat("V06_Cream_Frosting",PALETTE["cream"])
LAVENDER_GLOSS=new_principled("V06_Lavender_Gloss",PALETTE["lavender"],rough=.15,coat=.9)
CYAN_GLOSS=new_principled("V06_Candy_Cyan_Gloss",PALETTE["candy_cyan"],rough=.12,coat=.95)
MINT_GLOSS=new_principled("V06_Mint_Gloss",PALETTE["mint"],rough=.16,coat=.85)
PEACH_GLOSS=new_principled("V06_Peach_Gloss",PALETTE["peach"],rough=.17,coat=.85)
GOLD_PREMIUM=new_principled("V06_Gold_Trim",PALETTE["gold"],rough=.18,metallic=.72,coat=.55)
CHOCO_GLOSS=new_principled("V06_Chocolate_Gloss",PALETTE["chocolate"],rough=.12,coat=.92)
MILK_CHOCO_GLOSS=new_principled("V06_Milk_Chocolate_Gloss",PALETTE["milk_chocolate"],rough=.15,coat=.85)
IRIDESCENT=iridescent_mat("V06_Iridescent_Sugar_Glaze")
HEART_EMISSIVE=new_principled("V06_Heart_Gem",PALETTE["hot_pink"],rough=.08,coat=1.0,emission=PALETTE["bubblegum"],emission_strength=2.8)

# Map old v0.5 materials to the locked style palette.
MATERIAL_MAP={
    "Candy_Ground":BLUSH_GLOSS,
    "Candy_Path":BUBBLEGUM_GLOSS,
    "Chocolate":CHOCO_GLOSS,
    "Milk_Chocolate":MILK_CHOCO_GLOSS,
    "Gummy_Green":MINT_GLOSS,
    "Mint":MINT_GLOSS,
    "Cherry_Red":CHERRY_GLOSS,
    "Vanilla_Cream":CREAM_FROST,
    "Berry_Purple":LAVENDER_GLOSS,
    "Sugar_White":PEARL_FROST,
    "Candy_Blue":CYAN_GLOSS,
    "Lemon_Yellow":GOLD_PREMIUM,
    "Orange_Candy":PEACH_GLOSS,
    "Gingerbread":MILK_CHOCO_GLOSS,
    "Caramel_Gold":GOLD_PREMIUM,
    "Magic_Cyan":IRIDESCENT,
    "Magic_Magenta":HOT_PINK_GLOSS,
    "Magic_Lime":MINT_GLOSS,
    "Frosting_Cloud":PEARL_FROST,
}

for o in bpy.context.scene.objects:
    if o.type!="MESH": continue
    for slot in o.material_slots:
        if slot.material and slot.material.name in MATERIAL_MAP:
            slot.material=MATERIAL_MAP[slot.material.name]

# ---------------------------------------------------------------------------
# Geometry helpers for the real map.
# ---------------------------------------------------------------------------
def add_bevel(o,width=.16,segments=3):
    if not o or o.type!="MESH": return o
    mod=o.modifiers.new("V06_Soft_Candy_Bevel","BEVEL")
    mod.width=width; mod.segments=segments
    return o

def heart(name,loc,scale=1.0,material=HEART_EMISSIVE,rot=(math.radians(90),0,0),collection=PROPS):
    curve=bpy.data.curves.new(name+"_Curve","CURVE")
    curve.dimensions="2D"; curve.resolution_u=8; curve.bevel_resolution=3
    curve.extrude=.12*scale; curve.bevel_depth=.035*scale; curve.fill_mode="BOTH"
    sp=curve.splines.new("POLY")
    steps=64; sp.points.add(steps-1)
    for i in range(steps):
        t=math.tau*i/steps
        x=(16*math.sin(t)**3)/17.0
        y=(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))/17.0
        sp.points[i].co=(x*scale,y*scale,0,1)
    sp.use_cyclic_u=True
    o=bpy.data.objects.new(name,curve); collection.objects.link(o)
    o.location=loc; o.rotation_euler=rot; curve.materials.append(material)
    # Curves look good in Blender but must become meshes to survive GLB export.
    for s in bpy.context.selected_objects: s.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.convert(target="MESH")
    o=bpy.context.object
    o["catalog_skip"]=True
    return o

def bow(name,loc,scale=1.0,material=BLUSH_GLOSS,collection=PROPS,rot=(math.radians(90),0,0)):
    x,y,z=loc
    left=sphere(name+"_L",(x-.64*scale,y,z),.76*scale,material,collection,segments=22,scale=(1.05,.40,.72))
    right=sphere(name+"_R",(x+.64*scale,y,z),.76*scale,material,collection,segments=22,scale=(1.05,.40,.72))
    left.rotation_euler[1]=math.radians(-24); right.rotation_euler[1]=math.radians(24)
    knot=sphere(name+"_Knot",(x,y-.04*scale,z),.38*scale,HOT_PINK_GLOSS,collection,segments=20,scale=(1,.75,1))
    tail_l=cube(name+"_TailL",(x-.35*scale,y,z-.82*scale),(.26*scale,.12*scale,.65*scale),material,collection,rot=(0,math.radians(-18),math.radians(-10)))
    tail_r=cube(name+"_TailR",(x+.35*scale,y,z-.82*scale),(.26*scale,.12*scale,.65*scale),material,collection,rot=(0,math.radians(18),math.radians(10)))
    return join_objects(name,[left,right,knot,tail_l,tail_r],collection)

def road_segment(name,a,b,width=4.7):
    ax,ay=a; bx,by=b
    dx=bx-ax; dy=by-ay; length=math.hypot(dx,dy); ang=math.atan2(dy,dx)
    # cream border underneath
    border=cube(name+"_Border",((ax+bx)/2,(ay+by)/2,.37),(length/2+0.55,width/2+.48,.18),PEARL_FROST,ENV,rot=(0,0,ang))
    add_bevel(border,.48,6); border["catalog_skip"]=True
    road=cube(name,((ax+bx)/2,(ay+by)/2,.62),(length/2,width/2,.13),BUBBLEGUM_GLOSS,ENV,rot=(0,0,ang))
    add_bevel(road,.38,6); road["catalog_skip"]=True
    # narrow iridescent center ribbon
    stripe=cube(name+"_Iridescent",((ax+bx)/2,(ay+by)/2,.78),(length/2-.2,.20,.035),IRIDESCENT,ENV,rot=(0,0,ang))
    add_bevel(stripe,.13,3); stripe["catalog_skip"]=True
    return road

# Replace the disconnected visual feeling with a continuous premium candy route.
v06_route=[(-34,-25),(-25,-20),(-12,-10),(-20,3),(-28,18),(-5,4),(0,-2),(18,5),(28,24)]
for i in range(len(v06_route)-1):
    road_segment(f"V06_Gloss_Road_{i:02d}",v06_route[i],v06_route[i+1],4.5 if i<6 else 4.0)

# Gloss overlay on the Chocolate River, preserving the chocolate identity.
river_surface=cube("V06_Chocolate_River_Gloss",(18,5,.08),(4.76,21.75,.07),CHOCO_GLOSS,ENV)
add_bevel(river_surface,.38,5); river_surface["catalog_skip"]=True
for y in (-12,-4,4,12,20):
    heart(f"V06_River_Heart_{y}",(18,y,.34),.62,HEART_EMISSIVE,rot=(0,0,0),collection=ENV)

# Premium castle entrance treatment.
heart("V06_Castle_Heart",(28,18.10,5.35),1.55,HEART_EMISSIVE)
bow("V06_Castle_Bow",(28,18.00,8.20),1.05,BLUSH_GLOSS)
for sx in (-1,1):
    cyl(f"V06_Castle_Gold_Column_{sx}",(28+sx*3.9,18.35,3.25),.19,5.2,GOLD_PREMIUM,PROPS,vertices=20)
    sphere(f"V06_Castle_Gold_Finial_{sx}",(28+sx*3.9,18.35,6.0),.34,GOLD_PREMIUM,PROPS,segments=18)

# Plaza centerpiece with glassy heart + bow.
heart("V06_Plaza_Heart",(-12,-10,5.4),1.30,IRIDESCENT)
bow("V06_Plaza_Bow",(-12,-10,3.55),.80,BLUSH_GLOSS)
cyl("V06_Plaza_Gold_Pedestal",(-12,-10,1.30),1.18,2.2,GOLD_PREMIUM,PROPS,vertices=32)

# Spawn gate premium dressing.
heart("V06_Spawn_Heart",(-34,-22.05,7.10),1.02,HEART_EMISSIVE)
bow("V06_Spawn_Bow",(-34,-22.18,5.55),.88,BLUSH_GLOSS)
for sx in (-1,1):
    sphere(f"V06_Spawn_Cherry_{sx}",(-34+sx*5.25,-22.2,4.55),.74,CHERRY_GLOSS,PROPS,segments=24)
    cyl(f"V06_Spawn_Gold_Post_{sx}",(-34+sx*5.25,-22.2,2.35),.15,3.8,GOLD_PREMIUM,PROPS,vertices=18)

# Market stalls get physical bows and gold finials.
for i,(x,y) in enumerate([(-19,-15),(-14,-17),(-8,-16),(-4,-12)]):
    bow(f"V06_Market_Bow_{i}",(x,y-1.68,3.56),.47,BLUSH_GLOSS)
    for sx in (-1,1):
        sphere(f"V06_Market_Finial_{i}_{sx}",(x+sx*2.15,y,4.28),.17,GOLD_PREMIUM,PROPS,segments=14)

# Heart lantern rhythm along the main route.
lantern_points=[(-29,-22),(-21,-17),(-15,-12),(-18,-1),(-25,12),(-9,2),(7,1),(20,10),(25,18)]
for i,(x,y) in enumerate(lantern_points):
    post=cyl(f"V06_HeartLamp_Post_{i}",(x,y,1.75),.105,3.5,GOLD_PREMIUM,PROPS,vertices=14)
    post["catalog_skip"]=True
    heart(f"V06_HeartLamp_Gem_{i}",(x,y,3.75),.38,HEART_EMISSIVE,rot=(math.radians(90),0,0))

# Bow landmarks in the lollipop forest to tie the whole map together.
for i,(x,y) in enumerate([(-39,14),(-28,24),(-18,30)]):
    bow(f"V06_Forest_Bow_{i}",(x,y,3.4),.52,BLUSH_GLOSS)

# Smooth important blocky objects where safe.
for o in bpy.context.scene.objects:
    if o.type!="MESH": continue
    n=o.name.lower()
    if any(k in n for k in ("market","castle_gate","spawn_sign","candy_cart","gingerbread_shop")):
        add_bevel(o,.10,3)


# ---------------------------------------------------------------------------
# v0.6.1 density + finish pass after inspecting the real rendered map.
# ---------------------------------------------------------------------------

# Remove the old disconnected cookie-path disks from beauty/export; the glossy
# continuous route now carries navigation visually.
for o in bpy.context.scene.objects:
    if o.name.startswith("CookiePath_"):
        o.hide_render=True

# Smooth organic/candy meshes. This is a major visual upgrade over flat facets.
for o in bpy.context.scene.objects:
    if o.type=="MESH" and len(o.data.polygons) > 18:
        n=o.name.lower()
        if not any(k in n for k in ("ground","road","counter","board","blocker","body","crate","bin")):
            for p in o.data.polygons:
                p.use_smooth=True

def make_strawberry(name,loc,scale=1.0):
    x,y,z=loc
    berry=sphere(name+"_Berry",(x,y,z),1.0*scale,CHERRY_GLOSS,PROPS,segments=28,scale=(.86,.78,1.12))
    # tiny cream/gold sugar seeds
    seeds=[]
    for j,a in enumerate((0.25,1.15,2.10,3.10,4.05,5.00)):
        sx=x+math.cos(a)*.62*scale
        sy=y-.69*scale
        sz=z+.18*scale+math.sin(a)*.52*scale
        s=sphere(name+f"_Seed_{j}",(sx,sy,sz),.07*scale,GOLD_PREMIUM,PROPS,segments=10,scale=(.65,.35,1.0))
        s["catalog_skip"]=True; seeds.append(s)
    leaves=[]
    for j,a in enumerate((0,1.25,2.5,3.75,5.0)):
        leaf=cone(name+f"_Leaf_{j}",(x+math.cos(a)*.32*scale,y+math.sin(a)*.22*scale,z+1.04*scale),
                  .28*scale,.02,.66*scale,MINT_GLOSS,PROPS,vertices=8,rot=(math.radians(70),0,a))
        leaf["catalog_skip"]=True; leaves.append(leaf)
    return berry

def make_cotton_tree(name,loc,scale=1.0):
    x,y=loc
    trunk=cyl(name+"_Trunk",(x,y,2.0*scale),.28*scale,4.0*scale,GOLD_PREMIUM,PROPS,vertices=18)
    trunk["catalog_skip"]=True
    clouds=[]
    for j,(dx,dy,dz,r) in enumerate([
        (0,0,4.8,1.65),(-1.15,.15,4.55,1.15),(1.15,.12,4.6,1.20),
        (-.55,-.15,5.55,1.05),(.65,-.12,5.55,1.05)
    ]):
        c=sphere(name+f"_Cloud_{j}",(x+dx*scale,y+dy*scale,dz*scale),r*scale,
                 BLUSH_GLOSS if j%2==0 else PEARL_FROST,PROPS,segments=24,scale=(1.05,.86,.82))
        clouds.append(c)
    return join_objects(name,clouds,PROPS)

# Dense premium landscaping around the areas the beauty cameras actually see.
for i,(x,y,s) in enumerate([
    (-23,-12,.90),(-17,-7,.70),(-7,-13,.86),(-4,-5,.72),
    (19,18,.78),(24,16,.92),(34,18,.80),(37,25,.92),
    (-35,17,.72),(-30,29,.85),(-19,20,.74)
]):
    make_strawberry(f"V061_Strawberry_{i}",(x,y,1.05*s),s)

for i,(x,y,s) in enumerate([
    (-41,5,.85),(-36,10,.72),(-23,13,.78),(-16,18,.72),
    (12,21,.70),(17,27,.72),(39,27,.78),(42,13,.72)
]):
    make_cotton_tree(f"V061_CottonTree_{i}",(x,y),s)

# Cherry landscaping is cheap geometry but adds the strong cherry-red contrast
# visible in the approved reference.
for i,(x,y,z,s) in enumerate([
    (-28,-18,1.0,.70),(-18,-12,1.0,.58),(-8,-8,1.0,.62),
    (21,13,1.0,.58),(26,19,1.0,.68),(32,21,1.0,.62),(36,15,1.0,.56),
    (-30,20,1.0,.55),(-22,27,1.0,.58)
]):
    cherry=sphere(f"V061_Cherry_{i}",(x,y,z),s,CHERRY_GLOSS,PROPS,segments=24)
    stem=cyl(f"V061_CherryStem_{i}",(x+.18*s,y,z+.95*s),.055*s,1.15*s,GOLD_PREMIUM,PROPS,vertices=10,rot=(0,math.radians(-18),0))
    stem["catalog_skip"]=True

# Pink/white striped awning overlays make the plaza visually coherent.
for i,(x,y) in enumerate([(-19,-15),(-14,-17),(-8,-16),(-4,-12)]):
    for k in range(7):
        sx=x-2.25+k*.75
        matl=BLUSH_GLOSS if k%2==0 else PEARL_FROST
        slat=cube(f"V061_AwningStripe_{i}_{k}",(sx,y-1.50,3.43),(.34,.18,.30),matl,PROPS)
        slat["catalog_skip"]=True
    bow(f"V061_StallBow_{i}",(x,y-1.72,3.72),.42,BLUSH_GLOSS)

# Castle: icing rails, cherry finials and heart windows break up the primitive
# cylinder/cone silhouette and pull it toward the approved concept.
for j,z in enumerate((3.0,5.4,7.5)):
    ring=torus(f"V061_CastleIcingRing_{j}",(28,24,z),3.42 if j<2 else 3.0,.16,PEARL_FROST,PROPS)
    ring["catalog_skip"]=True
for j,(x,z) in enumerate(((24.8,3.2),(28,4.2),(31.2,3.2),(28,7.0))):
    heart(f"V061_CastleWindow_{j}",(x,18.04,z),.48 if j<3 else .62,
          HEART_EMISSIVE,rot=(math.radians(90),0,0))
for j,(x,y,z) in enumerate([
    (22,19,11.2),(34,19,11.2),(22,29,13.2),(34,29,13.2),(28,24,18.1)
]):
    sphere(f"V061_CastleCherry_{j}",(x,y,z),.50 if j<4 else .68,CHERRY_GLOSS,PROPS,segments=24)

# Add frosting dollops and hearts along the main plaza/castle approach.
for i,(x,y) in enumerate([(-10,-5),(-7,-1),(-2,1),(4,2),(10,3),(15,6),(20,11),(24,16)]):
    dollop=cone(f"V061_FrostDollop_{i}",(x,y,1.0),.85,.08,1.8,PEARL_FROST,PROPS,vertices=28)
    add_bevel(dollop,.09,3)
    heart(f"V061_PathHeart_{i}",(x+.9,y,.55),.28,HEART_EMISSIVE,rot=(0,0,0))

# Make the large world base visibly pink instead of neutral.
ground=bpy.data.objects.get("Candyland_Ground")
if ground and ground.type=="MESH":
    ground.data.materials.clear(); ground.data.materials.append(BLUSH_GLOSS)

# ---------------------------------------------------------------------------
# Dreamy real-render lighting / glow.
# ---------------------------------------------------------------------------
world=bpy.context.scene.world
if world and world.use_nodes:
    bg=world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value=(0.58,0.36,0.62,1)
        bg.inputs["Strength"].default_value=.72

bpy.ops.object.light_add(type="AREA",location=(-22,-24,32))
beauty=bpy.context.object; beauty.name="V06_Beauty_Key"; beauty.data.energy=3200; beauty.data.size=26; beauty.data.color=(1.0,.48,.67); look_at(beauty,(-6,-2,2))
bpy.ops.object.light_add(type="AREA",location=(38,18,26))
pearllight=bpy.context.object; pearllight.name="V06_Pearl_Fill"; pearllight.data.energy=2600; pearllight.data.size=22; pearllight.data.color=(.58,.72,1.0); look_at(pearllight,(18,12,4))
bpy.ops.object.light_add(type="AREA",location=(-22,30,22))
mintlight=bpy.context.object; mintlight.name="V06_Mint_Rim"; mintlight.data.energy=1500; mintlight.data.size=18; mintlight.data.color=(.52,1.0,.82); look_at(mintlight,(-26,20,4))

scene=bpy.context.scene
scene.render.resolution_x=1280; scene.render.resolution_y=720
try:
    scene.view_settings.look="AgX - Medium High Contrast"
except Exception:
    pass

# Compositor glow for emissive heart gems and specular highlights.
scene.use_nodes=True
nt=scene.node_tree
nt.nodes.clear()
rl=nt.nodes.new("CompositorNodeRLayers")
glare=nt.nodes.new("CompositorNodeGlare")
glare.glare_type="FOG_GLOW"; glare.quality="HIGH"; glare.threshold=.75; glare.size=6; glare.mix=-.82
comp=nt.nodes.new("CompositorNodeComposite")
nt.links.new(rl.outputs["Image"],glare.inputs["Image"]); nt.links.new(glare.outputs["Image"],comp.inputs["Image"])

shots=[
    ("candyland_iso",(92,-104,80),(0,3,4)),
    ("candyland_spawn_view",(-49,-46,13),(-20,-8,4)),
    ("candyland_castle_view",(58,-1,30),(28,24,7)),
    ("candyland_plaza_view",(-34,-34,18),(-12,-10,3.2)),
    ("candyland_forest_view",(-58,2,18),(-29,23,4.5)),
    ("candyland_river_view",(43,-20,18),(18,5,2.5)),
    ("candyland_gloss_closeup",(-26,-32,9),(-9,-7,3.0)),
]
for name,loc,target in shots:
    cam.location=loc; look_at(cam,target)
    scene.render.filepath=str(OUT/f"{name}.png")
    bpy.ops.render.render(write_still=True)

# ---------------------------------------------------------------------------
# Compatibility exports from the actually restyled map.
# ---------------------------------------------------------------------------
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

style_report={
    "version":"0.6.0",
    "style":"GLOSS_AND_GIRLY",
    "palette":{k:[round(c,4) for c in v] for k,v in PALETTE.items()},
    "material_library":[
        m.name for m in (BUBBLEGUM_GLOSS,HOT_PINK_GLOSS,CHERRY_GLOSS,BLUSH_GLOSS,
        PEARL_FROST,CREAM_FROST,LAVENDER_GLOSS,CYAN_GLOSS,MINT_GLOSS,PEACH_GLOSS,
        GOLD_PREMIUM,CHOCO_GLOSS,MILK_CHOCO_GLOSS,IRIDESCENT,HEART_EMISSIVE)
    ],
    "features":[
        "palette_enforcement","procedural_gloss_materials","iridescent_glaze",
        "continuous_gloss_route","premium_castle_entrance","plaza_heart_centerpiece",
        "premium_spawn_gate","market_bows_and_gold","heart_lantern_route",
        "dreamy_three_point_lighting","compositor_glow"
    ],
    "beauty_renders":[x[0]+".png" for x in shots],
    "visual_meshes":len(visual),
    "visual_triangles":sum(tri_count(o) for o in visual),
}
(OUT/"style_report.json").write_text(json.dumps(style_report,indent=2),encoding="utf-8")
report_path=OUT/"blender_report.json"
report=json.loads(report_path.read_text(encoding="utf-8"))
report.update({
    "version":"0.6.0",
    "status":"BLENDER_EXECUTED",
    "vision_pass":"GLOSS_AND_GIRLY_REAL_MAP_PASS",
    "visual_meshes":len(visual),
    "visual_triangles":sum(tri_count(o) for o in visual),
    "procedural_asset_objects":len(props),
    "style_report":"style_report.json",
    "beauty_renders":[x[0]+".png" for x in shots],
})
report_path.write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(style_report,indent=2))
