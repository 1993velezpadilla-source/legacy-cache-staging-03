"""Candyland Dream v0.2 modular blockout generator.

Prepared for Blender execution; does not claim runtime execution.
Adds reusable candy props, collision proxies, navigation markers, route gates,
and export-ready collection structure.

Usage:
    blender -b --python blender/build_candyland_v02.py
"""
import math
import bpy

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def collection(name):
    c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c

COL_ENV=collection("ENV")
COL_PROPS=collection("PROPS")
COL_COLLISION=collection("COLLISION")
COL_NAV=collection("NAV")
COL_GAMEPLAY=collection("GAMEPLAY")

def move_to(obj,col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)

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

def cube(name,loc,scale,material=None,col=COL_ENV,hide=False):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if material: o.data.materials.append(material)
    move_to(o,col); o.hide_render=hide
    return o

def cyl(name,loc,radius,depth,material=None,col=COL_PROPS,vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    o=bpy.context.object; o.name=name
    if material: o.data.materials.append(material)
    move_to(o,col); return o

# Environment + readable route
cube("Candyland_Ground",(0,0,-1),(48,36,1),PINK)
route=[(-34,-25),(-25,-20),(-12,-10),(-20,3),(-28,18),(0,-2),(18,5),(28,24)]
for i,(x,y) in enumerate(route):
    cube(f"Path_{i:02d}",(x,y,0.25),(4,2.5,0.25),PATH)

# River + traversal
cube("Chocolate_River",(18,5,-0.25),(5,22,0.25),CHOCO)
for i,y in enumerate([-12,-4,4,12,20]):
    cyl(f"Marshmallow_{i:02d}",(18,y,0.4),1.7,0.7,CREAM)

# Modular lollipop factory
def lollipop(i,x,y,height=8.0):
    cyl(f"Lollipop_Stem_{i:02d}",(x,y,height/2),0.45,height,GREEN)
    cyl(f"Lollipop_Candy_{i:02d}",(x,y,height+0.5),2.2,1.0,RED,vertices=32)
for i,p in enumerate([(-38,10),(-31,27),(-22,12),(-16,25),(-40,28),(-8,21)]):
    lollipop(i,*p)

# Plaza + castle
cyl("Candy_Plaza",(-12,-10,0.2),8,0.5,CREAM,vertices=48)
cyl("Plaza_Center_Candy",(-12,-10,1.4),2.5,2.0,RED,vertices=48)
cyl("Castle_Platform",(28,24,0.5),12,1.0,CREAM,vertices=48)
for i,(dx,dy,r,h) in enumerate([(-6,-5,2,8),(6,-5,2,8),(-6,5,2,10),(6,5,2,10),(0,0,3,14)]):
    cyl(f"Castle_Tower_{i:02d}",(28+dx,24+dy,h/2+1),r,h,PURPLE,vertices=32)

# Gameplay markers
spawn=cyl("Spawn_Marker",(-34,-25,0.8),2,0.4,RED,col=COL_GAMEPLAY,vertices=32)
spawn["role"]="player_spawn"
gate=cube("Castle_Gate_Blocker",(28,13,2.5),(4,0.5,2.5),CREAM,COL_GAMEPLAY)
gate["role"]="toggle_gate"; gate["default_locked"]=True

# Collision proxies: explicit and engine-neutral
cube("COL_MapBounds",(0,0,1),(48,36,2),None,COL_COLLISION,True)["collision_type"]="bounds_reference"
cube("COL_River",(18,5,0.1),(5,22,0.6),None,COL_COLLISION,True)["collision_type"]="hazard"
for i,(x,y) in enumerate([(-38,10),(-31,27),(-22,12),(-16,25),(-40,28),(-8,21)]):
    cyl(f"COL_Lollipop_{i:02d}",(x,y,4),1.0,8,None,COL_COLLISION,vertices=12)["collision_type"]="obstacle"

# Navigation route markers; engine importer can convert these to nav waypoints.
for i,(x,y) in enumerate(route):
    n=cyl(f"NAV_{i:02d}",(x,y,0.15),0.6,0.3,None,COL_NAV,vertices=12)
    n["nav_index"]=i; n["path_width"]=5.0
    n.hide_render=True

# Preview camera
bpy.ops.object.camera_add(location=(75,-85,70))
cam=bpy.context.object; cam.name="Preview_Camera"
cam.rotation_euler=(math.radians(58),0,math.radians(40))
bpy.context.scene.camera=cam

scene=bpy.context.scene
scene["CandylandDream_Status"]="PREPARED_NOT_EXECUTED"
scene["CandylandDream_Version"]="0.2.0"
scene["Player_Clearance_M"]=1.2
bpy.ops.wm.save_as_mainfile(filepath="candyland_dream_v02.blend")
