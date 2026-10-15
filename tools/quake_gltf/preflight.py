#!/usr/bin/env python3
"""Read-only GLB 2.0 preflight for NZ:P/Vril model migration (stdlib only).
This is NOT Khronos glTF-Validator or a GPU/runtime visual test.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942

def parse_glb(path):
    payload = path.read_bytes()
    if len(payload) < 20:
        raise ValueError("File too short to be a GLB 2.0 container")
    magic, version, length = struct.unpack_from("<4sII", payload, 0)
    if magic != b"glTF" or version != 2:
        raise ValueError("Not a valid GLB 2.0 header")
    if length != len(payload):
        raise ValueError(f"GLB length mismatch: header={length} actual={len(payload)}")
    offset, json_blob, bin_size = 12, None, None
    while offset < length:
        if offset + 8 > length:
            raise ValueError("Truncated chunk header")
        size, chunk_type = struct.unpack_from("<II", payload, offset)
        offset += 8
        if size % 4 or offset + size > length:
            raise ValueError("Chunk size misaligned or exceeds GLB length")
        chunk = payload[offset:offset + size]
        if chunk_type == JSON_CHUNK:
            if json_blob is not None:
                raise ValueError("Duplicate GLB JSON chunk")
            json_blob = chunk
        elif chunk_type == BIN_CHUNK:
            if bin_size is not None:
                raise ValueError("Duplicate GLB BIN chunk")
            bin_size = size
        offset += size
    if json_blob is None:
        raise ValueError("Missing GLB JSON chunk")
    document = json.loads(json_blob.rstrip(b"\x00 \x09\x0a\x0d").decode("utf8"))
    if document.get("asset", {}).get("version") != "2.0":
        raise ValueError("Missing asset.version=2.0")
    return document, bin_size

def determinant_3x3_column_major(m):
    a, b, c = m[0], m[4], m[8]
    d, e, f = m[1], m[5], m[9]
    g, h, i = m[2], m[6], m[10]
    return a * (e*i-f*h) - b * (d*i-f*g) + c * (d*h-e*g)

def node_local_reflection(node):
    if "matrix" in node:
        m = node["matrix"]
        return len(m) == 16 and determinant_3x3_column_major(m) < 0
    s = node.get("scale", [1, 1, 1])
    return len(s) == 3 and s[0] * s[1] * s[2] < 0

def inspect(doc, bin_size, triangle_limit=None):
    warnings = []
    meshes = doc.get("meshes", [])
    nodes = doc.get("nodes", [])
    accessors = doc.get("accessors", [])
    buffer_views = doc.get("bufferViews", [])
    buffers = doc.get("buffers", [])
    triangles, primitives = 0, 0
    if bin_size is not None and buffers and buffers[0].get("byteLength", 0) > bin_size:
        warnings.append("Declared BIN byteLength exceeds embedded BIN chunk")
    for i, bv in enumerate(buffer_views):
        bi = bv.get("buffer", 0)
        if bi >= len(buffers):
            warnings.append(f"bufferView {i} references missing buffer {bi}")
        elif bv.get("byteOffset", 0) + bv.get("byteLength", 0) > buffers[bi].get("byteLength", 0):
            warnings.append(f"bufferView {i} goes beyond buffer length")
    for mi, mesh in enumerate(meshes):
        for pi, p in enumerate(mesh.get("primitives", [])):
            primitives += 1
            if p.get("mode", 4) != 4:
                warnings.append(f"mesh {mi} primitive {pi} is not TRIANGLES")
                continue
            a = p.get("attributes", {})
            if "NORMAL" not in a:
                warnings.append(f"mesh {mi} primitive {pi} lacks NORMAL")
            if "TEXCOORD_0" not in a:
                warnings.append(f"mesh {mi} primitive {pi} lacks UV0")
            index = p.get("indices", a.get("POSITION"))
            if not isinstance(index, int) or not 0 <= index < len(accessors):
                warnings.append(f"mesh {mi} primitive {pi} has no valid position/index accessor")
                continue
            count = accessors[index].get("count", 0)
            if count % 3:
                warnings.append(f"mesh {mi} primitive {pi} count {count} not divisible by 3")
            triangles += count // 3
    if triangle_limit is not None and triangles > triangle_limit:
        warnings.append(f"Triangles {triangles} > specified budget {triangle_limit}; no geometry removed")
    mirrored = [i for i, n in enumerate(nodes) if node_local_reflection(n)]
    if mirrored:
        warnings.append("Mirrored LOCAL transforms on nodes " + str(mirrored) + "; inspect final world winding and culling")
    mats = doc.get("materials", [])
    return {
        "meshes": len(meshes), "primitives": primitives, "triangles": triangles,
        "nodes": len(nodes), "local_mirrored_nodes": mirrored,
        "skins": len(doc.get("skins", [])),
        "skin_joints": [len(s.get("joints", [])) for s in doc.get("skins", [])],
        "animations": [a.get("name", f"animation_{i}") for i,a in enumerate(doc.get("animations", []))],
        "materials": len(mats), "images": len(doc.get("images", [])),
        "alpha_modes": [m.get("alphaMode", "OPAQUE") for m in mats],
        "double_sided_materials": [i for i,m in enumerate(mats) if m.get("doubleSided", False)],
        "extensions_required": doc.get("extensionsRequired", []),
        "warnings": warnings,
        "limitations": ["No triangle winding or pixel rendering test", "No runtime capability claim", "No PBR equivalence check"],
    }

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("glb", type=Path)
    ap.add_argument("--triangle-budget", type=int, help="Warning only; no geometry decimation")
    args = ap.parse_args(argv)
    try:
        doc, bin_size = parse_glb(args.glb)
        report = inspect(doc, bin_size, args.triangle_budget)
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"file": str(args.glb), "error": str(exc)}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps({"file": str(args.glb), **report}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
