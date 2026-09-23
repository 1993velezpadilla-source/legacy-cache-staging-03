#!/usr/bin/env python3
"""CandyAssetScanner v0.7

CPU-capable production scanner:
1) open-vocabulary detection with GroundingDINO (Hugging Face implementation)
2) box-guided GrabCut segmentation fallback that runs on CPU
3) proxy GLB generation for every accepted detection
4) contact sheets + machine-readable manifests
5) quality queue for TRELLIS / TripoSR / Hunyuan3D GPU workers

The proxy meshes are intentionally conservative blockouts. High-quality
image-to-3D backends can replace them without changing the manifest contract.
"""
from __future__ import annotations
import argparse, json, math, os, re, sys, traceback
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh

PROMPTS = [
    "bow","cherry","strawberry","lollipop","heart candy","heart lantern",
    "candy sign","market stall","cupcake tower","castle tower","candy tree",
    "frosting rock","bridge","candy bench","crystal","gumdrop","donut",
]
ROUNDISH = {"cherry","strawberry","heart candy","crystal","gumdrop","donut"}
TALL = {"lollipop","heart lantern","candy tree","castle tower","cupcake tower"}
WIDE = {"bridge","market stall","candy bench","candy sign"}

def slug(s:str)->str:
    return re.sub(r"[^a-z0-9]+","_",s.lower()).strip("_")

def iou(a,b):
    ax1,ay1,ax2,ay2=a; bx1,by1,bx2,by2=b
    x1=max(ax1,bx1); y1=max(ay1,by1); x2=min(ax2,bx2); y2=min(ay2,by2)
    inter=max(0,x2-x1)*max(0,y2-y1)
    if inter<=0:return 0.0
    aa=max(1,(ax2-ax1)*(ay2-ay1)); bb=max(1,(bx2-bx1)*(by2-by1))
    return inter/(aa+bb-inter)

def nms(rows,thr=.55):
    rows=sorted(rows,key=lambda x:x["score"],reverse=True)
    keep=[]
    for r in rows:
        if all(iou(r["box"],k["box"])<thr or r["label"]!=k["label"] for k in keep):
            keep.append(r)
    return keep

def detect_grounding_dino(image:Image.Image, device="cpu"):
    from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
    import torch
    model_id=os.environ.get("CANDY_GDINO_MODEL","IDEA-Research/grounding-dino-tiny")
    processor=AutoProcessor.from_pretrained(model_id)
    model=AutoModelForZeroShotObjectDetection.from_pretrained(model_id).to(device)
    text=". ".join(PROMPTS)+"."
    inputs=processor(images=image,text=text,return_tensors="pt").to(device)
    with torch.no_grad():
        outputs=model(**inputs)
    # Transformers renamed box_threshold -> threshold in newer releases.
    kwargs=dict(
        text_threshold=float(os.environ.get("CANDY_TEXT_THRESHOLD","0.20")),
        target_sizes=[image.size[::-1]],
    )
    box_t=float(os.environ.get("CANDY_BOX_THRESHOLD","0.28"))
    try:
        results=processor.post_process_grounded_object_detection(
            outputs, inputs.input_ids, threshold=box_t, **kwargs
        )[0]
    except TypeError:
        results=processor.post_process_grounded_object_detection(
            outputs, inputs.input_ids, box_threshold=box_t, **kwargs
        )[0]
    out=[]
    for box,score,label in zip(results["boxes"],results["scores"],results["labels"]):
        b=[int(round(x)) for x in box.detach().cpu().tolist()]
        label=str(label).strip().lower().replace(".","")
        # normalize model phrases to our known asset vocabulary
        match=min(PROMPTS,key=lambda p: (0 if p in label or label in p else 1, abs(len(p)-len(label))))
        out.append({"box":b,"score":float(score.detach().cpu()),"label":match,"raw_label":label,"backend":"grounding_dino"})
    return nms(out)

def fallback_saliency(image:Image.Image):
    """Last-resort non-semantic region finder if model install/download fails."""
    rgb=np.array(image.convert("RGB"))
    hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
    sat=hsv[:,:,1]
    _,bw=cv2.threshold(sat,90,255,cv2.THRESH_BINARY)
    bw=cv2.morphologyEx(bw,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    n,labels,stats,_=cv2.connectedComponentsWithStats(bw)
    rows=[]
    H,W=bw.shape
    for i in range(1,n):
        x,y,w,h,area=[int(v) for v in stats[i]]
        if area < .0025*W*H or area > .25*W*H: continue
        rows.append({"box":[int(x),int(y),int(x+w),int(y+h)],"score":.15,"label":"candy prop","raw_label":"salient_region","backend":"saliency_fallback"})
    return rows[:24]

def segment_grabcut(rgb:np.ndarray,box):
    H,W=rgb.shape[:2]
    x1,y1,x2,y2=box
    pad=max(2,int(.04*max(x2-x1,y2-y1)))
    x1=max(1,x1-pad); y1=max(1,y1-pad); x2=min(W-2,x2+pad); y2=min(H-2,y2+pad)
    if x2-x1<8 or y2-y1<8: return None,(x1,y1,x2,y2)
    mask=np.zeros((H,W),np.uint8)
    bg=np.zeros((1,65),np.float64); fg=np.zeros((1,65),np.float64)
    rect=(x1,y1,max(2,x2-x1),max(2,y2-y1))
    try:
        cv2.grabCut(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),mask,rect,bg,fg,5,cv2.GC_INIT_WITH_RECT)
        binary=np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD),255,0).astype("uint8")
    except Exception:
        binary=np.zeros((H,W),np.uint8); binary[y1:y2,x1:x2]=255
    roi=binary[y1:y2,x1:x2]
    if roi.mean()<8:
        binary[y1:y2,x1:x2]=255
    return binary,(x1,y1,x2,y2)

def crop_rgba(rgb,mask,box):
    x1,y1,x2,y2=box
    arr=np.dstack([rgb,mask])
    return Image.fromarray(arr[y1:y2,x1:x2])

def ellipsoid_mesh(rx,ry,rz):
    m=trimesh.creation.icosphere(subdivisions=2,radius=1.0)
    m.apply_scale([rx,ry,rz]); return m

def proxy_mesh(label,aspect=1.0):
    """Create robust class-aware proxy geometry in meters."""
    parts=[]
    if label in ROUNDISH:
        parts=[ellipsoid_mesh(.8,max(.35,.8/aspect),.9)]
    elif label=="bow":
        left=ellipsoid_mesh(.8,.28,.48); left.apply_translation([-.72,0,0])
        right=ellipsoid_mesh(.8,.28,.48); right.apply_translation([.72,0,0])
        knot=ellipsoid_mesh(.35,.32,.35)
        parts=[left,right,knot]
    elif label in TALL:
        stem=trimesh.creation.cylinder(radius=.16,height=2.2,sections=20); stem.apply_translation([0,0,1.1])
        top=ellipsoid_mesh(.7,.36,.7); top.apply_translation([0,0,2.4])
        parts=[stem,top]
    elif label=="bridge":
        deck=trimesh.creation.box(extents=[3.6,1.4,.22]); deck.apply_translation([0,0,.35])
        rail1=trimesh.creation.box(extents=[3.6,.12,.7]); rail1.apply_translation([0,.72,.72])
        rail2=rail1.copy(); rail2.apply_translation([0,-1.44,0])
        parts=[deck,rail1,rail2]
    elif label in WIDE:
        body=trimesh.creation.box(extents=[2.4,1.2,1.6]); body.apply_translation([0,0,.8])
        roof=trimesh.creation.box(extents=[2.8,1.45,.18]); roof.apply_translation([0,0,1.85])
        parts=[body,roof]
    else:
        parts=[trimesh.creation.box(extents=[1.4,max(.5,1.4/aspect),1.4])]
    return trimesh.util.concatenate(parts)

def export_proxy(path,label,box):
    x1,y1,x2,y2=box
    aspect=max(.35,min(3.0,(x2-x1)/max(1,(y2-y1))))
    mesh=proxy_mesh(label,aspect)
    color={
        "bow":[255,105,180,255],"cherry":[220,15,55,255],"strawberry":[255,65,95,255],
        "lollipop":[255,90,190,255],"heart candy":[255,120,210,255],"crystal":[120,220,255,255],
        "candy tree":[255,160,220,255],"bridge":[210,150,80,255]
    }.get(label,[255,145,205,255])
    mesh.visual.vertex_colors=np.tile(color,(len(mesh.vertices),1))
    scene=trimesh.Scene(mesh)
    scene.export(str(path))

def build_contact(image:Image.Image,rows,out_path):
    canvas=image.convert("RGB").copy()
    d=ImageDraw.Draw(canvas)
    for i,r in enumerate(rows):
        x1,y1,x2,y2=r["box"]
        d.rectangle([x1,y1,x2,y2],outline=(255,255,255),width=3)
        txt=f'{i:02d} {r["label"]} {r["score"]:.2f}'
        tw=max(80,7*len(txt))
        d.rectangle([x1,max(0,y1-24),x1+tw,y1],fill=(30,12,38))
        d.text((x1+4,max(0,y1-21)),txt,fill=(255,235,248))
    canvas.save(out_path,quality=92)

def process_image(path:Path,out:Path,max_items:int):
    image=Image.open(path).convert("RGB")
    try:
        rows=detect_grounding_dino(image,device=os.environ.get("CANDY_DEVICE","cpu"))
        detector_error=None
    except Exception as e:
        detector_error=f"{type(e).__name__}: {e}"
        traceback.print_exc()
        rows=fallback_saliency(image)
    rows=rows[:max_items]
    rgb=np.array(image)
    img_dir=out/slug(path.stem); (img_dir/"crops").mkdir(parents=True,exist_ok=True); (img_dir/"masks").mkdir(exist_ok=True); (img_dir/"glb").mkdir(exist_ok=True)
    processed=[]
    for i,r in enumerate(rows):
        mask,box=segment_grabcut(rgb,r["box"])
        if mask is None: continue
        ident=f'{i:02d}_{slug(r["label"])}'
        crop=crop_rgba(rgb,mask,box)
        crop_path=img_dir/"crops"/f"{ident}.png"; crop.save(crop_path)
        Image.fromarray(mask[box[1]:box[3],box[0]:box[2]]).save(img_dir/"masks"/f"{ident}.png")
        glb_path=img_dir/"glb"/f"{ident}.glb"; export_proxy(glb_path,r["label"],box)
        r={**r,"id":ident,"source_image":path.name,"crop":str(crop_path.relative_to(out)),"proxy_glb":str(glb_path.relative_to(out))}
        processed.append(r)
    build_contact(image,processed,img_dir/"detections.jpg")
    return {"image":path.name,"detector_error":detector_error,"items":processed,"contact_sheet":str((img_dir/"detections.jpg").relative_to(out))}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input_dir"); ap.add_argument("output_dir")
    ap.add_argument("--max-items",type=int,default=18)
    args=ap.parse_args()
    inp=Path(args.input_dir); out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    images=[p for p in sorted(inp.rglob("*")) if p.suffix.lower() in {".png",".jpg",".jpeg",".webp"}]
    if not images: raise SystemExit(f"No images found under {inp}")
    reports=[process_image(p,out,args.max_items) for p in images]
    items=[x for r in reports for x in r["items"]]
    quality=[]
    for x in sorted(items,key=lambda z:z["score"],reverse=True):
        if x["label"] in {"bow","cherry","strawberry","lollipop","heart candy","heart lantern","candy sign","market stall","cupcake tower","castle tower","candy tree","frosting rock","bridge","candy bench","crystal","gumdrop","donut"}:
            quality.append({**x,"preferred_3d_backend":"TRELLIS","fast_backend":"TripoSR","texture_backend":"Hunyuan3D-2.1"})
    manifest={
        "version":"0.7.0","status":"SCANNER_COMPLETE","images":reports,
        "item_count":len(items),"quality_queue":quality[:30],
        "contract":{"proxy_glb":"always produced","high_quality_glb":"optional GPU replacement preserving item id"},
        "licenses":{
            "GroundingDINO":"Apache-2.0","SAM2_planned":"Apache-2.0",
            "TripoSR":"MIT","TRELLIS":"MIT majority; audit listed submodules","Hunyuan3D":"verify exact model license before redistribution"
        }
    }
    (out/"scanner_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    (out/"quality_queue.json").write_text(json.dumps(quality[:30],indent=2),encoding="utf-8")
    print(json.dumps({"status":"SCANNER_COMPLETE","images":len(images),"items":len(items),"quality_queue":len(quality[:30])},indent=2))

if __name__=="__main__": main()
