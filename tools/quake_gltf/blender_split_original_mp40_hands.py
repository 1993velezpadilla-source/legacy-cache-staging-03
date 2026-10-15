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
if len(args)!=5:
    raise SystemExit("USAGE original_mp40.mdl measured-transform.json hands_only.mdl report.json gun_pose.iqmpose")
source,fit_file,destination,report_file,pose_file=map(lambda p:Path(p).resolve(),args)
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
# Verify the selected HAND vertices, not just the full original weapon,
# actually change across QuakeC's published MP40 reload frames 4..31.
# Quake frame indices are zero-based; the real authoring timeline is preserved.
hand_vertex_ids=sorted({idx for i in selected for idx in faces[i][1:]})
ref_pose=frames[3]
moving_vertices=0
for vid in hand_vertex_ids:
    base_pose=ref_pose[28+vid*4:32+vid*4]
    if any(frames[k][28+vid*4:32+vid*4]!=base_pose for k in range(4,31)):
        moving_vertices+=1
moving_fraction=moving_vertices/len(hand_vertex_ids)
if moving_fraction<.15:
    raise RuntimeError("NZP_HANDS_RED original hand mesh is static through reload: "+
                       repr((moving_vertices,len(hand_vertex_ids),moving_fraction)))
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
 "hand_reloading_animated_vertex_count":moving_vertices,
 "hand_animated_vertex_fraction_during_reload":moving_fraction,
 "hand_animates_from_original_authored_46_frames":True,
 "all_46_source_pose_bytes_preserved":True,
 "skins_and_vertex_uvs_unchanged":True,
 "runtime_renderer_enabled":False,"visual_fidelity_verified":False}
report_file.parent.mkdir(parents=True,exist_ok=True)
# The extracted authentic hands use the ORIGINAL 46 stock poses.
# The modern replacement MP40 initially stayed fixed, apart from a made-up
# 11-degree pitch. Stock MP40 gun vertices REALLY rotate ~35 degrees during
# reload and translate ~17 Quake units. This is why the old hand animation
# appeared to float around the new stationary weapon on real Pixel Fold.
#
# Derive each stock gun's authoritative rigid root pose *from the 421 gun
# polygons REMOVED from the hands-only overlay*, not from guessed keyframes.
# All input MDL frame bytes remain unchanged. Fit transform X@R+t to
# reference frame 0 => source QuakeC frame. Ignore the independently moving
# old magazine outliers with a robust Kabsch fit.
gun_vertices=sorted(set(idx for tri in rejected for idx in faces[tri][1:])-
                    set(hand_vertex_ids))
if len(gun_vertices)<300:
    raise RuntimeError("NZP_GUN_POSE_RED too few isolated original gun vertices")
def dequantized(frame):
    packed=np.frombuffer(frame,dtype=np.uint8,count=nv*4,offset=28)
    return packed.reshape((nv,4))[:,:3].astype(np.float64)*scale+origin
ref=dequantized(frames[0])[gun_vertices]
def solve_pose(reference,target):
    active=np.arange(len(reference))
    for loop in range(4):
        X=reference[active];Y=target[active]
        xc=X.mean(axis=0);yc=Y.mean(axis=0)
        u,_,vt=np.linalg.svd((X-xc).T@(Y-yc),full_matrices=True)
        correction=np.diag([1.,1.,np.linalg.det(u@vt)])
        R=u@correction@vt
        translation=yc-xc@R
        residual=np.linalg.norm(reference@R+translation-target,axis=1)
        cutoff=max(0.4,float(np.quantile(residual,0.55))*2.5)
        next_active=np.where(residual<=cutoff)[0]
        if len(next_active)<len(reference)*0.70:
            break
        if np.array_equal(active,next_active):
            break
        active=next_active
    return R,translation,residual
records=[]
pose_blocks=[]
for frame_i,frame_bytes in enumerate(frames):
    target=dequantized(frame_bytes)[gun_vertices]
    R,t,err=solve_pose(ref,target)
    # OpenGL expects column-major matrices. The Kabsch row-vector map
    # X@R+t becomes column-vector R.T@X + t. Flatten in Fortran order.
    matrix=np.eye(4,dtype=np.float64)
    matrix[:3,:3]=R.T
    matrix[:3,3]=t
    flattened=matrix.flatten(order="F").tolist()
    pose_blocks.append(struct.pack("<16f",*flattened))
    degrees=math.degrees(math.acos(float(np.clip((np.trace(R)-1)/2,-1,1))))
    records.append({"frame":frame_i,"rotation_degrees":degrees,
                    "translation":list(map(float,t)),
                    "p90_rigid_error":float(np.quantile(err,.9)),
                    "median_rigid_error":float(np.median(err))})
peak_angle=max(x["rotation_degrees"] for x in records[4:32])
peak_distance=max(float(np.linalg.norm(x["translation"])) for x in records[4:32])
worst_p90=max(x["p90_rigid_error"] for x in records[4:32])
if not (25.0<peak_angle<80.0 and 8.0<peak_distance<65.0 and worst_p90<3.0):
    raise RuntimeError("NZP_GUN_POSE_RED unexpected original gun trajectory "+
                       repr((peak_angle,peak_distance,worst_p90)))
if not np.allclose(np.frombuffer(pose_blocks[0],dtype="<f4").reshape(4,4,order="F"),
                   np.eye(4),atol=.0001):
    raise RuntimeError("NZP_GUN_POSE_RED first frame should be identity")
pose_blob=b"XIQMPOSE"+struct.pack("<I",nframes)+b"".join(pose_blocks)
assert len(pose_blob)==12+nframes*64
pose_file.parent.mkdir(parents=True,exist_ok=True)
pose_file.write_bytes(pose_blob)
# Preserve the ORIGINAL stock NZ:P magazine's actual trajectory as well.
# Previously we made the 894-face MODERN mag follow invented down/side
# smoothsteps, even though the original hands were animated around a
# DIFFERENT clip path. The stock MDL frames carry that exact path.
#
# Isolate the elongated piece reaching the lowest Z of the ORIGINAL GUN.
# Do not use arbitrary source vertex indices: discover and validate the
# original mag's narrow X/Y footprint and 17-unit vertical extent.
base_frame=dequantized(frames[0])
gun_base=base_frame[gun_vertices]
lowest_z=float(gun_base[:,2].min())
mag_bottom=gun_base[gun_base[:,2]<lowest_z+0.5]
if not 3<=len(mag_bottom)<=12:
    raise RuntimeError("NZP_ORIGINAL_MAG_CLIP_RED ambiguous lowest gun piece")
low=mag_bottom.min(axis=0)
high=mag_bottom.max(axis=0)
clip_vertices=[i for i in gun_vertices
               if low[0]-0.5<=base_frame[i,0]<=high[0]+0.5
               and low[1]-0.5<=base_frame[i,1]<=high[1]+0.5
               and lowest_z-0.1<=base_frame[i,2]<=lowest_z+18]
clip_span=np.ptp(base_frame[clip_vertices],axis=0)
if not (8<=len(clip_vertices)<=26 and 2<clip_span[0]<6
        and 1<clip_span[1]<4 and 15<clip_span[2]<20):
    raise RuntimeError("NZP_ORIGINAL_MAG_CLIP_RED geometry insufficient "+
                       repr((len(clip_vertices),clip_span.tolist())))
stock_clip_reference=base_frame[clip_vertices].mean(axis=0)
clip_deltas=[]
clip_records=[]
for frame_i,frame_bytes in enumerate(frames):
    # Pose transforms reference MDL gun points into stock frame i;
    # recover the same row-vector matrix in source Quake coordinates.
    root=np.frombuffer(pose_blocks[frame_i],dtype="<f4").reshape((4,4),order="F")
    root_rot=root[:3,:3].T.astype(np.float64)
    root_t=root[:3,3].astype(np.float64)
    clip_center=dequantized(frame_bytes)[clip_vertices].mean(axis=0)
    expected=stock_clip_reference@root_rot+root_t
    # Compute magazine displacement IN THE LOCAL MOVING GUN frame.
    # The renderer divides this by the existing IQM->MDL fit_scale.
    local=(clip_center-expected)@root_rot.T
    if not np.isfinite(local).all() or np.max(np.abs(local))>65:
        raise RuntimeError("NZP_ORIGINAL_MAG_CLIP_RED bad keyframed displacement")
    clip_deltas.append(struct.pack("<3f",*map(float,local)))
    clip_records.append(list(map(float,local)))
largest=float(np.max(np.abs(np.asarray(clip_records)[4:32])))
if not (18<largest<48 and np.linalg.norm(clip_records[0])<.001
        and np.linalg.norm(clip_records[30])<.6):
    raise RuntimeError("NZP_ORIGINAL_MAG_CLIP_RED did not recover real reload movement "+str(largest))
clip_blob=b"XIQMCLIP"+struct.pack("<I",nframes)+b"".join(clip_deltas)
assert len(clip_blob)==12+nframes*12
clip_path=pose_file.with_suffix(".iqmclip")
clip_path.write_bytes(clip_blob)
report["original_magazine_clip_motion"]="AUTHENTIC_46_FRAME_SOURCE_GUN_LOCAL_CENTROID"
report["original_magazine_source_vertices"]=len(clip_vertices)
report["original_magazine_max_relative_motion_quake_units"]=largest
report["original_magazine_clip_file_sha256"]=hashlib.sha256(clip_blob).hexdigest()
report["original_magazine_clip_sidecar_bytes"]=len(clip_blob)
print("MP40_ORIGINAL_MAG_CLIP_46_KEYFRAMES_GREEN",len(clip_vertices),largest)
report["modern_weapon_follows_original_stock_gun_pose"]=True
report["stock_gun_pose_reference_frame"]=0
report["stock_gun_pose_max_rotation_degrees"]=peak_angle
report["stock_gun_pose_max_translation_quake_units"]=peak_distance
report["stock_gun_pose_worst_90pct_rigid_error"]=worst_p90
report["stock_gun_pose_sidecar_sha256"]=hashlib.sha256(pose_blob).hexdigest()
report["stock_gun_pose_sidecar_bytes"]=len(pose_blob)
report["source_gun_pose_validation_only_not_android_visual_certified"]=True
report_file.write_text(json.dumps(report,indent=2))
print("MP40_AUTHENTIC_SOURCE_HANDS_46_FRAME_SPLIT_GREEN",json.dumps(report))
print("MP40_STOCK_GUN_RIGID_POSE_46_FRAME_GREEN",
      peak_angle,peak_distance,worst_p90,len(pose_blob))
