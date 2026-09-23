#!/usr/bin/env python3
"""CandyAssetScanner reference detector.

AI-first:
  GroundingDINO through HuggingFace Transformers when available.
Safe fallback:
  approved bootstrap inventory + OpenCV GrabCut.

Outputs are deterministic enough for CI and explicitly record the backend used.
"""
from __future__ import annotations
import argparse, base64, hashlib, json, os, sys, traceback
from pathlib import Path

from PIL import Image, ImageDraw

PROMPTS = [
    "satin bow","cherry candy","strawberry candy","heart lantern","heart crystal",
    "lollipop tree","candy market stall","cupcake castle tower","candy signpost",
    "frosting rock","wafer bridge","candy bench"
]

CLASS_MAP = {
    "satin bow":"satin_bow","bow":"satin_bow",
    "cherry candy":"cherry","cherry":"cherry",
    "strawberry candy":"strawberry","strawberry":"strawberry",
    "heart lantern":"heart_lantern","heart lamp":"heart_lantern",
    "heart crystal":"heart_crystal","crystal heart":"heart_crystal",
    "lollipop tree":"lollipop_tree","lollipop":"lollipop_tree",
    "candy market stall":"market_stall","market stall":"market_stall",
    "cupcake castle tower":"cupcake_tower","castle tower":"cupcake_tower",
    "candy signpost":"signpost","signpost":"signpost",
    "frosting rock":"frosting_rock","frosting cliff":"frosting_rock",
    "wafer bridge":"wafer_bridge_decor","bridge":"wafer_bridge_decor",
    "candy bench":"candy_bench","bench":"candy_bench",
}

def decode_reference(src: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix == ".b64":
        raw = base64.b64decode("".join(src.read_text().split()))
        out.write_bytes(raw)
        return out
    out.write_bytes(src.read_bytes())
    return out

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def clamp_box(box,w,h):
    x1,y1,x2,y2=box
    x1=max(0,min(w-2,int(x1))); y1=max(0,min(h-2,int(y1)))
    x2=max(x1+1,min(w,int(x2))); y2=max(y1+1,min(h,int(y2)))
    return [x1,y1,x2,y2]

def seed_detections(seed_path: Path, w: int, h: int):
    seed=json.loads(seed_path.read_text())
    out=[]
    for d in seed["detections"]:
        x1,y1,x2,y2=d["bbox"]
        out.append({
            **d,
            "bbox_px":clamp_box([x1*w,y1*h,x2*w,y2*h],w,h),
            "source":"approved_seed"
        })
    return out

def ai_detections(image_path: Path, min_score: float):
    # Import lazily. Hosted CI can install these; normal CPU-only local runs can skip.
    import torch
    from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
    model_id=os.environ.get("CANDY_GROUNDING_DINO_MODEL","IDEA-Research/grounding-dino-tiny")
    image=Image.open(image_path).convert("RGB")
    processor=AutoProcessor.from_pretrained(model_id)
    model=AutoModelForZeroShotObjectDetection.from_pretrained(model_id)
    model.eval()
    text=". ".join(PROMPTS)+"."
    inputs=processor(images=image,text=text,return_tensors="pt")
    with torch.no_grad():
        outputs=model(**inputs)
    target_sizes=[(image.height,image.width)]
    results=processor.post_process_grounded_object_detection(
        outputs,
        inputs.input_ids,
        box_threshold=min_score,
        text_threshold=max(.18,min_score-.08),
        target_sizes=target_sizes,
    )[0]
    detections=[]
    labels=results.get("text_labels",results.get("labels",[]))
    for box,score,label in zip(results["boxes"],results["scores"],labels):
        if not isinstance(label,str):
            try: label=PROMPTS[int(label)]
            except Exception: label=str(label)
        key=min(CLASS_MAP, key=lambda k: 0 if k in label.lower() else 999)
        cls=CLASS_MAP.get(key,"unknown") if key in label.lower() else CLASS_MAP.get(label.lower(),"unknown")
        if cls=="unknown":
            continue
        b=[float(x) for x in box.tolist()]
        detections.append({
            "label":label,
            "class":cls,
            "bbox_px":clamp_box(b,image.width,image.height),
            "score":round(float(score),4),
            "priority":7,
            "source":"groundingdino"
        })
    return detections, model_id

def nms_by_class(dets, iou_threshold=.55):
    def iou(a,b):
        ax1,ay1,ax2,ay2=a; bx1,by1,bx2,by2=b
        ix1=max(ax1,bx1); iy1=max(ay1,by1); ix2=min(ax2,bx2); iy2=min(ay2,by2)
        inter=max(0,ix2-ix1)*max(0,iy2-iy1)
        aa=max(1,(ax2-ax1)*(ay2-ay1)); ba=max(1,(bx2-bx1)*(by2-by1))
        return inter/(aa+ba-inter)
    out=[]
    for cls in sorted({d["class"] for d in dets}):
        group=sorted([d for d in dets if d["class"]==cls],key=lambda d:d["score"],reverse=True)
        keep=[]
        for d in group:
            if all(iou(d["bbox_px"],k["bbox_px"])<iou_threshold for k in keep):
                keep.append(d)
        out.extend(keep)
    return sorted(out,key=lambda d:(-d.get("priority",0),-d["score"]))

def make_cutouts(image_path: Path, detections, out_dir: Path):
    out_dir.mkdir(parents=True,exist_ok=True)
    image=Image.open(image_path).convert("RGBA")
    try:
        import cv2, numpy as np
        bgr=cv2.cvtColor(np.array(image.convert("RGB")),cv2.COLOR_RGB2BGR)
        use_cv=True
    except Exception:
        use_cv=False
    for i,d in enumerate(detections):
        x1,y1,x2,y2=d["bbox_px"]
        crop=image.crop((x1,y1,x2,y2))
        cut=crop
        seg_backend="box_crop"
        if use_cv and (x2-x1)>8 and (y2-y1)>8:
            try:
                roi=bgr[y1:y2,x1:x2].copy()
                mask=np.zeros(roi.shape[:2],np.uint8)
                bg=np.zeros((1,65),np.float64); fg=np.zeros((1,65),np.float64)
                rect=(1,1,max(1,roi.shape[1]-2),max(1,roi.shape[0]-2))
                cv2.grabCut(roi,mask,rect,bg,fg,3,cv2.GC_INIT_WITH_RECT)
                alpha=np.where((mask==2)|(mask==0),0,255).astype("uint8")
                rgba=cv2.cvtColor(roi,cv2.COLOR_BGR2RGBA)
                rgba[:,:,3]=alpha
                cut=Image.fromarray(rgba)
                seg_backend="opencv_grabcut"
            except Exception:
                pass
        fn=f"{i:02d}_{d['class']}.png"
        cut.save(out_dir/fn)
        d["cutout"]=f"crops/{fn}"
        d["segmentation_backend"]=seg_backend

def draw_preview(image_path: Path, detections, out_path: Path):
    im=Image.open(image_path).convert("RGB")
    draw=ImageDraw.Draw(im)
    for d in detections:
        x1,y1,x2,y2=d["bbox_px"]
        draw.rectangle((x1,y1,x2,y2),outline=(255,255,255),width=max(1,im.width//240))
        draw.text((x1+2,y1+2),f"{d['class']} {d['score']:.2f}",fill=(255,255,255))
    im.resize((max(640,im.width*2),max(360,im.height*2))).save(out_path)

def build_queue(detections):
    best={}
    for d in detections:
        cls=d["class"]
        if cls not in best or (d.get("priority",0),d["score"])>(best[cls].get("priority",0),best[cls]["score"]):
            best[cls]=d
    return [{
        "class":cls,
        "source_detection":d.get("cutout"),
        "priority":d.get("priority",5),
        "requested_3d_backends":["trellis","triposr","procedural_blender"],
        "fallback_backend":"procedural_blender"
    } for cls,d in sorted(best.items(),key=lambda kv:-kv[1].get("priority",0))]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reference-b64",type=Path,required=True)
    ap.add_argument("--seed",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--min-score",type=float,default=.28)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    reference=decode_reference(args.reference_b64,args.out/"reference.jpg")
    image=Image.open(reference)
    backend="approved_seed"
    model_id=None
    errors=[]
    detections=[]
    if os.environ.get("CANDY_USE_AI_DETECTOR","1")!="0":
        try:
            detections,model_id=ai_detections(reference,args.min_score)
            if len(detections)<3:
                raise RuntimeError(f"AI detector returned only {len(detections)} usable detections")
            backend="groundingdino"
        except Exception as e:
            errors.append({"stage":"groundingdino","error":repr(e),"trace":traceback.format_exc(limit=2)})
    if not detections:
        detections=seed_detections(args.seed,image.width,image.height)
    detections=nms_by_class(detections)
    make_cutouts(reference,detections,args.out/"crops")
    draw_preview(reference,detections,args.out/"detection_preview.png")
    queue=build_queue(detections)
    report={
        "schema_version":1,
        "status":"SCANNER_OK",
        "reference_sha256":sha256(reference),
        "reference_size":[image.width,image.height],
        "detection_backend":backend,
        "model_id":model_id,
        "segmentation_policy":"OpenCV GrabCut fallback; SAM2 adapter supported separately",
        "detections":detections,
        "asset_queue":queue,
        "errors":errors
    }
    (args.out/"detections.json").write_text(json.dumps(report,indent=2))
    (args.out/"asset_queue.json").write_text(json.dumps({"assets":queue},indent=2))
    print(json.dumps({"status":"SCANNER_OK","backend":backend,"detections":len(detections),"queued_assets":len(queue)},indent=2))

if __name__=="__main__":
    main()
