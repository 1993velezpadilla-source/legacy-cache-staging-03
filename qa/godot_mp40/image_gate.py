#!/usr/bin/env python3
"""Fail-closed pixel validation on real Godot image outputs; never use fake frames."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("captures")
labels = ("00-background", "01-hip", "02-ads-pose", "03-inspect")
imgs = {}
report = {"status": "RED", "source": "Godot screenshot pixel inspection", "frames": {}, "comparisons": {}}
for name in labels:
    f = root / (name + ".png")
    if not f.is_file():
        raise SystemExit("RED missing image: " + str(f))
    im = Image.open(f).convert("RGB")
    if im.width < 640 or im.height < 360:
        raise SystemExit("RED viewport too small: " + str(im.size))
    v = np.asarray(im, dtype=np.float32) / 255.0
    lum = float(v.mean())
    report["frames"][name] = {"resolution": [im.width, im.height], "luminance": round(lum, 4)}
    if lum < 0.025:
        raise SystemExit("RED black image: " + name)
    imgs[name] = v
h, w = imgs[labels[0]].shape[:2]
roi = np.s_[int(h * .12):int(h * .95), int(w * .14):int(w * .86)]
for a, b in (("00-background", "01-hip"), ("00-background", "02-ads-pose"), ("01-hip", "02-ads-pose"), ("02-ads-pose", "03-inspect")):
    d = np.max(np.abs(imgs[a][roi] - imgs[b][roi]), axis=2)
    changed = int((d > .065).sum())
    avg = round(float(d.mean()), 5)
    key = a + "_vs_" + b
    report["comparisons"][key] = {"pixels_changed": changed, "mean_difference": avg}
    if changed < 2000 or avg < .002:
        (root / "image_gate_report.json").write_text(json.dumps(report, indent=2))
        raise SystemExit(f"RED invisible/unchanged: {key} changed={changed} mean={avg}")
report["status"] = "GREEN_NATIVE_SOURCE_RENDER_ONLY"
(root / "image_gate_report.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
