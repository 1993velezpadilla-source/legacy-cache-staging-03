#!/usr/bin/env python3
"""Isolate genuine 46-frame NZ:P animated hands from its original MP40 MDL.

Launch Blender with nzp-team/assets source/models/weapons/mp40/v_mp40/mesh.blend.
The source armature's vertex groups identify stock gun vs. real hands. The
source-to-shipping-MDL transform is measured, not eyeballed. For the ORIGINAL
MDL, remove only gun triangles: all animated frame bytes, indexed skin, tex
coords, vertices, and original pose names remain bit-for-bit unchanged.

No replacement gun is fabricated; the output is a companion hands-only MDL
which is NOT enabled in Vril until its geometry is validated visually.
"""
import bpy
import hashlib
import json
import math
import numpy as np
import struct
import sys
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree

args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=4:
    raise SystemExit("USAGE original_mp40.mdl measured-transform.json hands_only.mdl report.json")
source,fit_file,destination,report_file=map(lambda p:Path(p).resolve(),args)
raw=source.read_bytes()
if len(raw)<84 or raw[:4]!=b"IDPO" or struct.unpack_from("<I",raw,4)[0]!=6:
    raise RuntimeError("NZP_HANDS_RED not original MDL v6")
skins,w,h,nv,nt,nframes=struct.unpack_from("<6I",raw,48)
if not (1<=skins<=8 and 1<=w<=2048 and 1<=h<=2048 and
        200<=nv<=4000 and 500<=nt<=4000 and nframes==46):
    raise RuntimeError("NZP_HANDS_RED unexpected original topology or frame count")
scale=np.array(struct.unpack_from("<3f",raw,8),dtype=float)
origin=np.array(struct.unpack_from("<3f",raw,20),dtype=float)
p=84
for _ in range(skins):
    if p+4>len(raw) or struct.unpack_from("<I",raw,p)[0]!=0:
        raise RuntimeError("NZP_HANDS_RED grouped skin unsupported")
    p+=4+w*h
skin_section=raw[84:p]
stverts=raw[p:p+12*nv]
if len(stverts)!=12*nv:raise RuntimeError("NZP_HANDS_RED truncated UV coordinates")
p+=12*nv
tri_start=p
tri_section=raw[p:p+16*nt]
if len(tri_section)!=16*nt:raise RuntimeError("NZP_HANDS_RED truncated faces")
faces=[struct.unpack_from("<4I",tri_section,16*i) for i in range(nt)]
if any(max(face[1:])>=nv for face in faces):
    raise RuntimeError("NZP_HANDS_RED out-of-range face vertices")
p+=16*nt
frame_start=p
frames=[]
for i in range(nframes):
    if p+28+4*nv>len(raw) or struct.unpack_from("<I",raw,p)[0]!=0:
        raise RuntimeError("NZP_HANDS_RED incomplete or grouped frame "+str(i))
    q=p+28
    if i==0:
        points=np.array([[raw[q+4*v+a]*scale[a]+origin[a] for a in range(3)]
                         for v in range(nv)],dtype=float)
    frames.append(raw[p:p+28+4*nv])
    p+=28+4*nv
if p!=len(raw):raise RuntimeError("NZP_HANDS_RED unexpected trailing MDL data")

fit=json.loads(fit_file.read_text())
if fit["reference_mdl_sha256"]!=hashlib.sha256(raw).hexdigest():
    raise RuntimeError("NZP_HANDS_RED source MDL hash disagrees with fit")
registration=fit["best"]
S=float(registration["scale"])
R=np.array(registration["rotation"],dtype=float)
T=np.array(registration["translation"],dtype=float)
if not (math.isfinite(S) and .01<S<100 and np.isfinite(R).all() and np.isfinite(T).all()):
    raise RuntimeError("NZP_HANDS_RED invalid measured source registration")
obj=bpy.data.objects.get("nzp_hands.ms3d.mo")
if obj is None or obj.type!="MESH":
    raise RuntimeError("NZP_HANDS_RED original authored mesh is missing")
groups={g.index:g.name for g in obj.vertex_groups}
if not {"Body","Slide","Clip"}.issubset(set(groups.values())):
    raise RuntimeError("NZP_HANDS_RED source gun/clip/bolt vertex groups absent")
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh=evaluated.to_mesh()
mesh.calc_loop_triangles()
src=np.array([list(evaluated.matrix_world@v.co) for v in mesh.vertices])
src=(src@R)*S+T
source_gun_kd=KDTree(len(mesh.loop_triangles))
source_hand_kd=KDTree(len(mesh.loop_triangles))
gun_id=hand_id=0
gun_names={"Body","Slide","Clip"}
# The polygon's predominant vertex-group influence determines whether
# it's legacy gun metal or original animated hands. No positional shortcuts.
for tri in mesh.loop_triangles:
    weights={}
    for vid in tri.vertices:
        for link in obj.data.vertices[vid].groups:
            if link.weight>.01:
                name=groups.get(link.group,"")
                weights[name]=weights.get(name,0.0)+link.weight
    if not weights:raise RuntimeError("NZP_HANDS_RED unclassified authored triangle")
    role=max(weights,key=weights.get)
    centroid=src[list(tri.vertices)].mean(axis=0)
    if role in gun_names:
        source_gun_kd.insert(Vector(centroid),gun_id)
        gun_id+=1
    else:
        source_hand_kd.insert(Vector(centroid),hand_id)
        hand_id+=1
evaluated.to_mesh_clear()
if gun_id<100 or hand_id<100:
    raise RuntimeError("NZP_HANDS_RED could not identify both source pieces")
source_gun_kd.balance()
source_hand_kd.balance()
bbox=float(np.linalg.norm(points.max(axis=0)-points.min(axis=0)))
if bbox<=0:raise RuntimeError("NZP_HANDS_RED empty original frame")
selected=[]
rejected=[]
uncertain=[]
normalized=[]
for i,face in enumerate(faces):
    coords=points[list(face[1:])]
    c=coords.mean(axis=0)
    _,_,d_hand=source_hand_kd.find(Vector(c))
    _,_,d_gun=source_gun_kd.find(Vector(c))
    nearest=min(d_hand,d_gun)/bbox
    normalized.append(float(nearest))
    if abs(d_hand-d_gun)<.003*bbox:
        uncertain.append(i)
    if d_hand<d_gun:
        selected.append(i)
    else:
        rejected.append(i)
# A truly conflicting triangle is unacceptable: never draw stray legacy
# gun components on top of the new 14.5k-triangle IQM.
if not (120<=len(selected)<=550 and len(rejected)>=200):
    raise RuntimeError("NZP_HANDS_RED suspicious hands-vs-gun segmentation "+
                       repr((len(selected),len(rejected))))
if len(uncertain)>int(.10*nt) or np.quantile(normalized,.90)>.075:
    raise RuntimeError("NZP_HANDS_RED proximity ambiguity requires review "+
                       repr((len(uncertain),float(np.quantile(normalized,.90)))))
face_blob=b"".join(tri_section[16*i:16*(i+1)] for i in selected)
header=bytearray(raw[:84])
struct.pack_into("<I",header,64,len(selected))
new=bytes(header)+skin_section+stverts+face_blob+b"".join(frames)
destination.parent.mkdir(parents=True,exist_ok=True)
destination.write_bytes(new)
ntris=struct.unpack_from("<I",new,64)[0]
assert ntris==len(selected)
assert new[-len(b"".join(frames)):]==raw[frame_start:]
report={
 "status":"AUTHENTIC_NZP_HANDS_ONLY_MDL_GENERATED_NOT_ANDROID_CERTIFIED",
 "input_sha256":hashlib.sha256(raw).hexdigest(),
 "output_sha256":hashlib.sha256(new).hexdigest(),
 "source_animated_frames":nframes,
 "source_polygons":nt,"hands_polygons":len(selected),
 "removed_legacy_gun_polygons":len(rejected),
 "uncertain_polygon_count":len(uncertain),
 "nearest_centroid_error_p90_bbox":float(np.quantile(normalized,.90)),
 "source_authored_hand_triangles":hand_id,
 "source_authored_gun_triangles":gun_id,
 "all_46_source_pose_bytes_preserved":True,
 "skins_and_vertex_uvs_unchanged":True,
 "runtime_renderer_enabled":False,"visual_fidelity_verified":False}
report_file.parent.mkdir(parents=True,exist_ok=True)
report_file.write_text(json.dumps(report,indent=2))
print("MP40_AUTHENTIC_SOURCE_HANDS_46_FRAME_SPLIT_GREEN",json.dumps(report))
