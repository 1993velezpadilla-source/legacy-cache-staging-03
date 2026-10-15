#!/usr/bin/env python3
"""Lossless GLB base-color image extraction for XZIEL IQM material sidecars.

No image recompression or downsizing. The output directory should be the same
directory as the .iqm; the Vril IQM preview searches for <material>.png|.jpg.
This is asset-preparation only: no content is shipped to production by default.
"""
import argparse
import base64
import hashlib
import json
import shutil
import struct
from pathlib import Path

from preflight import parse_glb

def _bin_chunk(path):
    blob = path.read_bytes()
    pos = 12
    while pos + 8 <= len(blob):
        size, tag = struct.unpack_from("<II", blob, pos)
        pos += 8
        if tag == 0x004E4942:
            return blob[pos:pos+size]
        pos += size
    return b""

def _safe_name(name):
    return "".join(ch if (ch.isascii() and (ch.isalnum() or ch in "_.-")) else "_" for ch in name)[:95]

def _get_image_data(glb, doc, image):
    if "bufferView" in image:
        bv = doc["bufferViews"][image["bufferView"]]
        if bv.get("buffer", 0) != 0:
            raise ValueError("External bufferView is not supported for GLB image")
        raw = _bin_chunk(glb)
        start = bv.get("byteOffset", 0)
        end = start + bv["byteLength"]
        if end > len(raw):
            raise ValueError("Image bufferView out of bounds")
        return raw[start:end], image.get("mimeType")
    uri = image.get("uri")
    if uri and uri.startswith("data:"):
        meta, payload = uri.split(",", 1)
        if not meta.endswith(";base64"):
            raise ValueError("Only base64 data URI supported")
        return base64.b64decode(payload, validate=True), meta[5:-7]
    if uri and not uri.startswith("/") and ".." not in Path(uri).parts:
        p = glb.parent / uri
        return p.read_bytes(), None
    raise ValueError("No safe readable image source")

def extract(glb, output, force=False):
    doc, _ = parse_glb(glb)
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for i, material in enumerate(doc.get("materials", [])):
        pbr = material.get("pbrMetallicRoughness", {})
        texref = pbr.get("baseColorTexture")
        if texref is None:
            continue
        texture_index = texref["index"]
        texture = doc["textures"][texture_index]
        image = doc["images"][texture["source"]]
        img, declared = _get_image_data(glb, doc, image)
        # Derive format from signature; reject ambiguous/malformed attachments.
        if img.startswith(b"\x89PNG\r\n\x1a\n"):
            suffix, actual = ".png", "image/png"
        elif img.startswith(b"\xff\xd8\xff"):
            suffix, actual = ".jpg", "image/jpeg"
        else:
            raise ValueError(f"Unsupported base color data in material {i}")
        if declared and declared != actual:
            raise ValueError(f"MIME mismatch in material {i}: {declared} vs {actual}")
        name = _safe_name(material.get("name", f"material_{i}"))
        if not name:
            raise ValueError("Empty sanitized material name")
        dest = output / (name + suffix)
        if dest.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {dest}. Use --force intentionally.")
        dest.write_bytes(img)
        records.append({
            "material": material.get("name", f"material_{i}"),
            "texture_path": str(dest), "bytes": len(img),
            "sha256": hashlib.sha256(img).hexdigest(), "resolution_changed": False
        })
    return records

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glb", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    a=parser.parse_args()
    try:
        r=extract(a.glb,a.output,a.force)
    except (OSError, ValueError, IndexError, KeyError) as exc:
        parser.exit(2, f"Texture extraction failed: {exc}\n")
    print(json.dumps(r,indent=2))
if __name__=="__main__":
    main()
