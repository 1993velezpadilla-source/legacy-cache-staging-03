#!/usr/bin/env python3
"""Export Candyland Dream as a conservative NZ:P/Vril smoke-test MAP."""
import json, os
from pathlib import Path

OUT=Path(os.environ.get("NZP_MAP_OUT","candyland/out/engine/candyland_harness.map"))
OUT.parent.mkdir(parents=True,exist_ok=True)
S=32

def kv(k,v):
    return f'"{k}" "{v}"\n'

def brush_box(mn,mx,texture="null"):
    x1,y1,z1=map(int,mn); x2,y2,z2=map(int,mx)
    x2=max(x2,x1+1); y2=max(y2,y1+1); z2=max(z2,z1+1)
    planes=[
      ((x1,y1,z1),(x1,y1+1,z1),(x1,y1,z1+1),texture,"[ 0 -1 0 0 ]","[ 0 0 -1 0 ]"),
      ((x1,y1,z1),(x1,y1,z1+1),(x1+1,y1,z1),texture,"[ 1 0 0 0 ]","[ 0 0 -1 0 ]"),
      ((x1,y1,z1),(x1+1,y1,z1),(x1,y1+1,z1),texture,"[ -1 0 0 0 ]","[ 0 -1 0 0 ]"),
      ((x2,y2,z2),(x2,y2+1,z2),(x2+1,y2,z2),texture,"[ 1 0 0 0 ]","[ 0 -1 0 0 ]"),
      ((x2,y2,z2),(x2+1,y2,z2),(x2,y2,z2+1),texture,"[ -1 0 0 0 ]","[ 0 0 -1 0 ]"),
      ((x2,y2,z2),(x2,y2,z2+1),(x2,y2+1,z2),texture,"[ 0 1 0 0 ]","[ 0 0 -1 0 ]"),
    ]
    s="{\n"
    for p1,p2,p3,t,u,v in planes:
        s+=f"( {p1[0]} {p1[1]} {p1[2]} ) ( {p2[0]} {p2[1]} {p2[2]} ) ( {p3[0]} {p3[1]} {p3[2]} ) {t} {u} {v} 0 1 1\n"
    return s+"}\n"

def point(classname,origin,props=None):
    s="{\n"+kv("classname",classname)
    for k,v in (props or {}).items():
        s+=kv(k,v)
    s+=kv("origin",f"{origin[0]} {origin[1]} {origin[2]}")+"}\n"
    return s

def q(x,y,z=0):
    return (int(x*S),int(y*S),int(z*S))

parts=[
    "// Candyland Dream NZ:P smoke harness\n",
    "{\n",
    kv("mapversion","220"),
    kv("classname","worldspawn"),
    kv("message","CANDYLAND DREAM - Xziel runtime harness"),
    kv("chaptertitle","CANDYLAND DREAM"),
    kv("location","Candy Dreamscape"),
    kv("person","Volnox"),
    kv("wad","../../textures/wad/zhlt.wad;../../textures/wad/Example_02.wad"),
]
wx1,wy1,wz1=q(-50,-38,0); wx2,wy2,wz2=q(50,38,12); wall=16
parts += [
    brush_box((wx1,wy1,-wall),(wx2,wy2,0),"tiles_me"),
    brush_box((wx1,wy1,wz2),(wx2,wy2,wz2+wall),"ceilings_64"),
    brush_box((wx1-wall,wy1,0),(wx1,wy2,wz2),"facility_wall_l"),
    brush_box((wx2,wy1,0),(wx2+wall,wy2,wz2),"facility_wall_l"),
    brush_box((wx1,wy1-wall,0),(wx2,wy1,wz2),"facility_wall_l"),
    brush_box((wx1,wy2,0),(wx2,wy2+wall,wz2),"facility_wall_l"),
]
for x,y in [(-34,-25),(-25,-20),(-12,-10),(-20,3),(-28,18),(0,-2),(18,5),(28,24)]:
    X,Y,_=q(x,y,0)
    parts.append(brush_box((X-64,Y-48,0),(X+64,Y+48,8),"tiles_me"))
for x,y,h in [(-38,10,8),(-31,27,8),(-22,12,8),(-16,25,8),(-40,28,8),(-8,21,8)]:
    X,Y,_=q(x,y,0)
    parts.append(brush_box((X-12,Y-12,0),(X+12,Y+12,int(h*S)),"facility_wall_l"))
X,Y,_=q(28,24,0)
parts.append(brush_box((X-180,Y-160,0),(X+180,Y+160,96),"facility_wall_l"))
parts.append("}\n")

base=q(-34,-25,1.2)
for i,(dx,dy) in enumerate([(-24,-24),(24,-24),(-24,24),(24,24)],1):
    parts.append(point(f"info_player_{i}_spawn",(base[0]+dx,base[1]+dy,base[2]+40),{
        "weapon":"0","currentmag":"0","currentammo":"0","angle":"45"
    }))

zmn=q(-45,-33,0.1); zmx=q(-8,2,4)
parts.append("{\n"+kv("classname","spawn_zone")+kv("zone_name","candy_start")+kv("adjacent_zones","")+kv("zone_target","candy_zombies")+brush_box(zmn,zmx,"trigger")+"}\n")
parts.append(point("spawn_zombie",q(-46,-25,1),{"spawnflags":"0","targetname":"candy_zombies","target":"candy_path"}))
parts.append(point("path_corner",q(-39,-25,1),{"wait":"0","spawnflags":"0","targetname":"candy_path"}))
parts.append(point("light",q(-12,-10,6),{"_light":"500","wait":"1","style":"0"}))
parts.append(point("light",q(28,24,8),{"_light":"450","wait":"1","style":"0"}))

OUT.write_text("".join(parts),encoding="utf-8")
text=OUT.read_text()
assert text.count("{")==text.count("}") and "worldspawn" in text and "spawn_zone" in text
summary={"map":str(OUT),"scale_units_per_meter":S,"players":4,"spawn_zones":1,"brace_balance":0,"status":"ENGINE_HARNESS_EXPORTED"}
(OUT.parent/"candyland_harness_export.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
