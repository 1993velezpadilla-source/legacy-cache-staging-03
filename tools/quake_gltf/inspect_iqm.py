#!/usr/bin/env python3
"""Validate an IQM2 binary and compare key structural counts with a source GLB.
No renderer is involved; structural parity alone NEVER proves visual fidelity.
"""
import argparse
import json
import struct
from pathlib import Path
from preflight import parse_glb, inspect

FIELDS = (
    "version filesize flags num_text ofs_text num_meshes ofs_meshes "
    "num_vertexarrays num_vertexes ofs_vertexarrays num_triangles ofs_triangles "
    "ofs_adjacency num_joints ofs_joints num_poses ofs_poses num_anims ofs_anims "
    "num_frames num_framechannels ofs_frames ofs_bounds num_comment ofs_comment "
    "num_extensions ofs_extensions"
).split()

def _checked_range(blob, offset, size, label):
    if offset < 0 or size < 0 or offset > len(blob) or size > len(blob) - offset:
        raise ValueError(f"{label} range exceeds IQM file")
    return blob[offset: offset + size]

def parse_iqm(path):
    blob = path.read_bytes()
    if len(blob) < 124:
        raise ValueError("IQM file too short")
    magic, *nums = struct.unpack_from("<16s27I", blob, 0)
    if magic != b"INTERQUAKEMODEL\x00":
        raise ValueError("Wrong IQM magic")
    header = dict(zip(FIELDS, nums))
    if header["version"] != 2:
        raise ValueError("Only IQM version 2 supported")
    if header["filesize"] != len(blob):
        raise ValueError("IQM size disagrees with header")
    section_sizes = {
        "meshes": 24, "vertexarrays": 20, "triangles": 12,
        "joints": 48, "poses": 88, "anims": 20, "extensions": 16
    }
    for section, stride in section_sizes.items():
        n = header["num_" + section]
        # Extensions are a linked-list, not a contiguous array.
        if section == "extensions":
            continue
        if n:
            _checked_range(blob, header["ofs_" + section], n * stride, section)
    if header["num_text"]:
        _checked_range(blob, header["ofs_text"], header["num_text"], "text")
    if header["num_frames"] and header["num_framechannels"]:
        _checked_range(blob, header["ofs_frames"],
                       2 * header["num_frames"] * header["num_framechannels"], "frames")
    if header["num_vertexarrays"] and header["num_vertexes"]:
        # IQM vertex array descriptor: type, flags, format, size, offset.
        for i in range(header["num_vertexarrays"]):
            raw = _checked_range(blob, header["ofs_vertexarrays"] + i*20, 20, "vertexarray")
            typ, flags, fmt, width, offset = struct.unpack("<5I", raw)
            # Typed attribute payload validation would require format-size handling.
            if width == 0:
                raise ValueError(f"vertexarray {i} has zero width")
    mesh_names = []
    text_blob = _checked_range(blob, header["ofs_text"], header["num_text"], "text")
    def read_name(index):
        if index >= len(text_blob):
            raise ValueError(f"Invalid string offset {index}")
        end = text_blob.find(b"\x00", index)
        if end < 0:
            raise ValueError("Unterminated IQM string")
        return text_blob[index:end].decode("utf8", errors="replace")
    for i in range(header["num_meshes"]):
        buf = _checked_range(blob, header["ofs_meshes"] + i*24, 24, "mesh")
        name, mat, firstv, numv, firstt, numt = struct.unpack("<6I",buf)
        if firstv + numv > header["num_vertexes"] or firstt + numt > header["num_triangles"]:
            raise ValueError(f"mesh {i} out of bounds")
        mesh_names.append({"name": read_name(name), "material":read_name(mat),
                           "vertices":numv,"triangles":numt})
    anim_names = []
    for i in range(header["num_anims"]):
        name, first, count, fps, flags = struct.unpack(
            "<IIIfI", _checked_range(blob, header["ofs_anims"] + i*20,20,"anim"))
        if first+count > header["num_frames"]:
            raise ValueError(f"animation {i} frames out of bounds")
        anim_names.append({"name":read_name(name), "frames":count, "fps":fps})
    return {
        "vertices": header["num_vertexes"],
        "triangles": header["num_triangles"],
        "meshes": mesh_names,
        "joints": header["num_joints"],
        "animations": anim_names,
        "frames": header["num_frames"],
        "file_bytes":len(blob)
    }

def compare(glb, iqm):
    source = inspect(*parse_glb(glb))
    target = parse_iqm(iqm)
    errors = []
    if source["triangles"] != target["triangles"]:
        errors.append(f"Triangle loss/change: GLB={source['triangles']} IQM={target['triangles']}")
    if source["skins"] and not target["joints"]:
        errors.append("Source GLB has skin but IQM has zero joints")
    if source["animations"] and not target["animations"]:
        errors.append("Source GLB has animations but IQM has zero animations")
    # Some exporters collapse multiple glTF nodes or merge/resegment meshes;
    # do not equate mesh count with visual material parity.
    return {"source": source, "converted": target, "structural_errors": errors,
            "NOTE":"This is NOT a UV, material, animation-pose, normals or visual parity test."}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("iqm", type=Path)
    ap.add_argument("--source-glb", type=Path)
    args = ap.parse_args()
    try:
        report = compare(args.source_glb,args.iqm) if args.source_glb else parse_iqm(args.iqm)
    except (OSError, ValueError, UnicodeError) as error:
        print(json.dumps({"error":str(error)}, indent=2))
        return 2
    print(json.dumps(report, indent=2))
    return 1 if report.get("structural_errors") else 0
if __name__ == "__main__":
    raise SystemExit(main())
