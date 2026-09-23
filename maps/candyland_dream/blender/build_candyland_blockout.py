"""Candyland Dream starter blockout generator.

Prepared for Blender execution. It creates placeholder geometry only.
It does NOT claim Blender execution.

Usage:
    blender -b --python build_candyland_blockout.py
"""

import math
import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def mat(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    return m

MAT_GROUND = mat("Candy_Ground", (0.96, 0.55, 0.72))
MAT_PATH = mat("Rainbow_Path", (0.95, 0.35, 0.55))
MAT_WATER = mat("Chocolate_River", (0.20, 0.06, 0.025))
MAT_GREEN = mat("Gummy_Green", (0.35, 0.90, 0.35))
MAT_CANDY = mat("Lollipop_Red", (1.0, 0.15, 0.35))
MAT_CREAM = mat("Castle_Cream", (1.0, 0.82, 0.55))
MAT_CUPCAKE = mat("Cupcake_Purple", (0.70, 0.35, 1.0))

def cube(name, loc, scale, material):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    return o

def cylinder(name, loc, radius, depth, material, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(material)
    return o

# Ground and main route.
cube("Candyland_Ground", (0, 0, -1.0), (48, 36, 1), MAT_GROUND)
path_points = [(-34,-25),(-25,-20),(-12,-10),(-20,3),(-28,18),(0,-2),(18,5),(28,24)]
for i, (x, y) in enumerate(path_points):
    cube(f"Path_{i:02d}", (x, y, 0.25), (4, 2.5, 0.25), MAT_PATH)

# Chocolate river and stepping stones.
cube("Chocolate_River", (18, 5, -0.25), (5, 22, 0.25), MAT_WATER)
for i, y in enumerate([-12, -4, 4, 12, 20]):
    cylinder(f"Marshmallow_{i:02d}", (18, y, 0.4), 1.7, 0.7, MAT_CREAM)

# Lollipop forest.
for i, (x, y) in enumerate([(-38,10),(-31,27),(-22,12),(-16,25),(-40,28),(-8,21)]):
    cylinder(f"Lollipop_Stem_{i:02d}", (x, y, 4), 0.45, 8, MAT_GREEN)
    cylinder(f"Lollipop_Candy_{i:02d}", (x, y, 8.5), 2.2, 1.0, MAT_CANDY)

# Plaza.
cylinder("Candy_Plaza", (-12, -10, 0.2), 8, 0.5, MAT_CREAM, 48)
cylinder("Plaza_Center_Candy", (-12, -10, 1.4), 2.5, 2.0, MAT_CANDY, 48)

# Cupcake Castle.
cylinder("Castle_Platform", (28, 24, 0.5), 12, 1.0, MAT_CREAM, 48)
for i, (dx, dy, r, h) in enumerate([
    (-6,-5,2,8),(6,-5,2,8),(-6,5,2,10),(6,5,2,10),(0,0,3,14)
]):
    cylinder(f"Castle_Tower_{i:02d}", (28+dx, 24+dy, h/2+1), r, h, MAT_CUPCAKE)

cylinder("Spawn_Marker", (-34, -25, 0.8), 2.0, 0.4, MAT_CANDY, 32)

bpy.ops.object.camera_add(location=(75, -85, 70))
cam = bpy.context.object
cam.rotation_euler = (math.radians(58), 0, math.radians(40))
bpy.context.scene.camera = cam

bpy.context.scene["CandylandDream_Status"] = "PREPARED_NOT_EXECUTED"
bpy.context.scene["CandylandDream_Version"] = "0.1.0"
bpy.ops.wm.save_as_mainfile(filepath="candyland_dream_blockout.blend")
