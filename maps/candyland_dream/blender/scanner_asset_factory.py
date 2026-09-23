"""CandyAssetScanner Blender 3D factory.

Reads scanner asset_queue.json and produces:
- candy_scanner_assets.blend
- candy_scanner_assets.glb
- scanner_asset_preview.png
- scanner_asset_factory_report.json

The procedural backend is the guaranteed CI fallback. AI-generated GLB files can
be dropped into CANDY_AI_3D_DIR using <class>.glb names; those are imported first.
"""
import bpy, json, math, os, hashlib
from pathlib import Path
from mathutils import Vector

QUEUE=Path(os.environ.get("CANDY_SCANNER_QUEUE","candyland/scanner/asset_queue.json"))
OUT=Path(os.environ.get("CANDY_SCANNER_3D_OUT","candyland/scanner3d"))
AI_DIR=Path(os.environ.get("CANDY_AI_3D_DIR","candyland/scanner/ai3d"))
OUT.mkdir(parents=True,exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def mat(name,color,rough=.16,metallic=0.0,coat=.9):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    if bs:
        bs.inputs["Base Color"].default_value=(*color,1)
        bs.inputs["Roughness"].default_value=rough
        bs.inputs["Metallic"].default_value=metallic
        if "Coat Weight" in bs.inputs: bs.inputs["Coat Weight"].default_value=coat
        if "Coat Roughness" in bs.inputs: bs.inputs["Coat Roughness"].default_value=.05
        if "Clearcoat" in bs.inputs: bs.inputs["Clearcoat"].default_value=coat
    return m

PINK=mat("Scanner_Bubblegum",(1.0,.24,.62),.10)
BLUSH=mat("Scanner_Blush",(1.0,.63,.78),.16)
RED=mat("Scanner_Cherry",(.82,.015,.10),.08)
CREAM=mat("Scanner_Cream",(1.0,.91,.86),.34,0,.35)
GOLD=mat("Scanner_Gold",(1.0,.53,.08),.17,.72,.55)
CYAN=mat("Scanner_Cyan",(.28,.87,1.0),.10)
MINT=mat("Scanner_Mint",(.52,1.0,.80),.14)
LAV=mat("Scanner_Lavender",(.72,.46,1.0),.14)
CHOCO=mat("Scanner_Chocolate",(.22,.035,.018),.12)
COOKIE=mat("Scanner_Wafer",(.78,.43,.16),.42)

def apply(o,m):
    if o.type=="MESH":
        o.data.materials.clear(); o.data.materials.append(m)
    return o

def bevel(o,w=.08,seg=3):
    if o.type=="MESH":
        b=o.modifiers.new("Scanner_SoftBevel","BEVEL"); b.width=w; b.segments=seg
    return o

def smooth(o):
    if o.type=="MESH":
        for p in o.data.polygons: p.use_smooth=True
    return o

def cube(n,loc,scale,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot)
    o=bpy.context.object; o.name=n; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return bevel(apply(o,m),min(scale)*.12,3)

def sphere(n,loc,r,m,scale=(1,1,1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r, location=loc)
    o=bpy.context.object; o.name=n; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return smooth(apply(o,m))

def cyl(n,loc,r,depth,m,rot=(0,0,0),verts=28):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object; o.name=n
    return bevel(smooth(apply(o,m)),min(r*.16,.10),2)

def cone(n,loc,r1,r2,depth,m,rot=(0,0,0),verts=32):
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r1,radius2=r2,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object; o.name=n
    return bevel(smooth(apply(o,m)),.05,2)

def torus(n,loc,major,minor,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=40,minor_segments=14,location=loc,rotation=rot)
    o=bpy.context.object; o.name=n
    return smooth(apply(o,m))

def heart(n,loc,s=1.0,m=PINK,rot=(math.radians(90),0,0)):
    curve=bpy.data.curves.new(n+"_Curve","CURVE"); curve.dimensions="2D"; curve.resolution_u=8
    curve.extrude=.12*s; curve.bevel_depth=.035*s; curve.bevel_resolution=3; curve.fill_mode="BOTH"
    sp=curve.splines.new("POLY"); steps=64; sp.points.add(steps-1)
    for i in range(steps):
        t=math.tau*i/steps
        x=(16*math.sin(t)**3)/17; y=(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))/17
        sp.points[i].co=(x*s,y*s,0,1)
    sp.use_cyclic_u=True
    o=bpy.data.objects.new(n,curve); bpy.context.scene.collection.objects.link(o); o.location=loc; o.rotation_euler=rot
    curve.materials.append(m)
    bpy.context.view_layer.objects.active=o; o.select_set(True); bpy.ops.object.convert(target="MESH"); o=bpy.context.object
    return bevel(o,.035*s,2)

def bow(n,loc,s=1.0):
    x,y,z=loc
    objs=[
        sphere(n+"_L",(x-.62*s,y,z),.72*s,BLUSH,scale=(1.05,.42,.72)),
        sphere(n+"_R",(x+.62*s,y,z),.72*s,BLUSH,scale=(1.05,.42,.72)),
        sphere(n+"_K",(x,y-.03*s,z),.36*s,PINK,scale=(1,.75,1)),
        cube(n+"_TL",(x-.34*s,y,z-.80*s),(.24*s,.10*s,.64*s),BLUSH,rot=(0,math.radians(-18),math.radians(-10))),
        cube(n+"_TR",(x+.34*s,y,z-.80*s),(.24*s,.10*s,.64*s),BLUSH,rot=(0,math.radians(18),math.radians(10))),
    ]
    return objs

def strawberry(n,loc,s=1.0):
    x,y,z=loc; objs=[sphere(n+"_Berry",(x,y,z),1*s,RED,scale=(.86,.78,1.12))]
    for i,a in enumerate((0,1.25,2.5,3.75,5.0)):
        objs.append(cone(n+f"_Leaf{i}",(x+math.cos(a)*.32*s,y+math.sin(a)*.20*s,z+1.05*s),.28*s,.02,.60*s,MINT,rot=(math.radians(70),0,a),verts=8))
    return objs

def cherry(n,loc,s=1.0):
    x,y,z=loc
    return [
        sphere(n+"_Fruit",(x,y,z),.85*s,RED),
        cyl(n+"_Stem",(x+.18*s,y,z+1.05*s),.055*s,1.15*s,GOLD,rot=(0,math.radians(-15),0),verts=10)
    ]

def lollipop_tree(n,loc,s=1.0):
    x,y,z=loc
    return [
        cyl(n+"_Stick",(x,y,z+2.3*s),.14*s,4.6*s,CREAM),
        torus(n+"_Candy",(x,y,z+5.0*s),1.25*s,.38*s,PINK,rot=(math.radians(90),0,0)),
        torus(n+"_Stripe",(x,y-.02*s,z+5.0*s),.72*s,.12*s,CREAM,rot=(math.radians(90),0,0)),
    ]

def market_stall(n,loc,s=1.0):
    x,y,z=loc; objs=[
        cube(n+"_Counter",(x,y,z+1.0*s),(1.9*s,1.1*s,.9*s),COOKIE),
        cube(n+"_Top",(x,y,z+3.2*s),(2.25*s,1.35*s,.20*s),PINK),
    ]
    for sx in (-1,1):
        objs.append(cyl(n+f"_Post{sx}",(x+sx*1.85*s,y,z+2.05*s),.10*s,3.2*s,GOLD))
    objs += bow(n+"_Bow",(x,y-1.33*s,z+3.15*s),.45*s)
    return objs

def cupcake_tower(n,loc,s=1.0):
    x,y,z=loc
    objs=[cyl(n+"_Wrapper",(x,y,z+1.7*s),1.7*s,3.4*s,LAV,verts=32)]
    for i,(dx,dy,dz,r,m) in enumerate([(0,0,3.6,1.8,CREAM),(-.5,0,4.45,1.15,BLUSH),(.55,0,4.45,1.1,PINK)]):
        objs.append(sphere(n+f"_Frost{i}",(x+dx*s,y+dy*s,z+dz*s),r*s,m,scale=(1,1,.62)))
    objs += cherry(n+"_Cherry",(x,y,z+5.55*s),.42*s)
    return objs

def signpost(n,loc,s=1.0):
    x,y,z=loc; objs=[cyl(n+"_Post",(x,y,z+1.8*s),.11*s,3.6*s,GOLD)]
    for i,(zz,ang,m) in enumerate(((2.8,-.12,PINK),(3.5,.10,BLUSH),(4.2,-.08,LAV))):
        objs.append(cube(n+f"_Board{i}",(x+.45*s,y,z+zz*s),(1.25*s,.14*s,.34*s),m,rot=(0,0,ang)))
    objs.append(heart(n+"_Heart",(x,y,z+4.8*s),.42*s,PINK,rot=(math.radians(90),0,0)))
    return objs

def frosting_rock(n,loc,s=1.0):
    x,y,z=loc; objs=[]
    for i,(dx,dy,dz,r) in enumerate(((0,0,.55,1.3),(-.85,.12,.45,.85),(.82,.05,.50,.92),(-.25,-.35,1.15,.78),(.50,-.30,1.1,.72))):
        objs.append(sphere(n+f"_Puff{i}",(x+dx*s,y+dy*s,z+dz*s),r*s,CREAM,scale=(1.12,.95,.72)))
    return objs

def wafer_bridge_decor(n,loc,s=1.0):
    x,y,z=loc; objs=[]
    for i in range(7):
        objs.append(cube(n+f"_Wafer{i}",(x+(i-3)*.62*s,y,z+.45*s),(.27*s,1.3*s,.16*s),COOKIE))
    for side in (-1,1):
        objs.append(cyl(n+f"_Rail{side}",(x,y+side*1.5*s,z+1.4*s),.10*s,4.4*s,CREAM,rot=(0,math.radians(90),0)))
    return objs

def candy_bench(n,loc,s=1.0):
    x,y,z=loc
    return [
        cube(n+"_Seat",(x,y,z+1.1*s),(1.8*s,.55*s,.18*s),PINK),
        cube(n+"_Back",(x,y+.45*s,z+1.85*s),(1.8*s,.16*s,.70*s),BLUSH),
        cyl(n+"_LegL",(x-1.35*s,y,z+.55*s),.12*s,1.0*s,GOLD),
        cyl(n+"_LegR",(x+1.35*s,y,z+.55*s),.12*s,1.0*s,GOLD),
    ]

BUILDERS={
 "satin_bow":lambda n,l,s:bow(n,l,s),
 "cherry":lambda n,l,s:cherry(n,l,s),
 "strawberry":lambda n,l,s:strawberry(n,l,s),
 "heart_lantern":lambda n,l,s:[cyl(n+"_Post",(l[0],l[1],l[2]+1.7*s),.10*s,3.4*s,GOLD),heart(n+"_Heart",(l[0],l[1],l[2]+3.7*s),.42*s,PINK)],
 "heart_crystal":lambda n,l,s:[heart(n,l,.85*s,CYAN,rot=(math.radians(90),0,0))],
 "lollipop_tree":lambda n,l,s:lollipop_tree(n,l,s),
 "market_stall":lambda n,l,s:market_stall(n,l,s),
 "cupcake_tower":lambda n,l,s:cupcake_tower(n,l,s),
 "signpost":lambda n,l,s:signpost(n,l,s),
 "frosting_rock":lambda n,l,s:frosting_rock(n,l,s),
 "wafer_bridge_decor":lambda n,l,s:wafer_bridge_decor(n,l,s),
 "candy_bench":lambda n,l,s:candy_bench(n,l,s),
}

def try_import_ai(cls,base_x):
    p=AI_DIR/f"{cls}.glb"
    if not p.exists(): return None
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(p))
    new=[o for o in bpy.data.objects if o not in before and o.type=="MESH"]
    if not new: return None
    for o in new: o.location.x += base_x
    return new

queue=json.loads(QUEUE.read_text())["assets"]
manifest=[]
spacing=7.0
for i,item in enumerate(queue):
    cls=item["class"]; x=(i-(len(queue)-1)/2)*spacing
    objs=try_import_ai(cls,x)
    backend="ai_glb" if objs else "procedural_blender"
    if not objs:
        builder=BUILDERS.get(cls)
        if not builder: continue
        objs=builder("SCAN_"+cls,(x,0,0),1.0)
    for o in objs:
        if hasattr(o,"__setitem__"):
            o["scanner_class"]=cls; o["scanner_backend"]=backend
    manifest.append({"class":cls,"backend":backend,"mesh_objects":sum(1 for o in objs if getattr(o,"type",None)=="MESH")})

# floor and studio
cube("ScannerFloor",(0,0,-.35),(max(8,len(queue)*spacing/2+4),5,.25),CREAM)
world=bpy.context.scene.world or bpy.data.worlds.new("ScannerWorld"); bpy.context.scene.world=world; world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.16,.06,.15,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.55

bpy.ops.object.light_add(type="AREA",location=(-5,-8,14)); key=bpy.context.object; key.data.energy=2200; key.data.size=12; key.data.color=(1,.45,.68)
bpy.ops.object.light_add(type="AREA",location=(9,4,10)); fill=bpy.context.object; fill.data.energy=1600; fill.data.size=10; fill.data.color=(.42,.72,1)
bpy.ops.object.camera_add(location=(0,-32,18)); cam=bpy.context.object
cam.rotation_euler=(Vector((0,0,2.4))-cam.location).to_track_quat("-Z","Y").to_euler(); cam.data.lens=48
scene=bpy.context.scene; scene.camera=cam; scene.render.resolution_x=1600; scene.render.resolution_y=720; scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"; scene.render.filepath=str(OUT/"scanner_asset_preview.png")
try: scene.render.engine="BLENDER_EEVEE_NEXT"
except Exception: scene.render.engine="BLENDER_EEVEE"
bpy.ops.render.render(write_still=True)

# exports
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"candy_scanner_assets.blend"))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(OUT/"candy_scanner_assets.glb"),export_format="GLB",use_selection=True,export_apply=True)

report={"status":"SCANNER_3D_OK","assets":manifest,"asset_count":len(manifest),"ai_dir":str(AI_DIR)}
(OUT/"scanner_asset_factory_report.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
