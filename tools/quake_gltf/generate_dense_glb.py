#!/usr/bin/env python3
"""Generate a fully indexed 20,000 triangle GLB fixture; NO game IP.
Used only to prove that GLB->IQM source geometry is not decimated by converter.
"""
import json
import math
import struct
from pathlib import Path

def make_dense_glb(path, width=101):
    if width < 2 or width > 220:
        raise ValueError("width must be 2..220")
    data = bytearray()
    views = []
    def chunk(blob, target):
        while len(data) % 4:
            data.append(0)
        offset = len(data)
        data.extend(blob)
        views.append({"buffer":0,"byteOffset":offset,"byteLength":len(blob),"target":target})
        return len(views)-1
    positions = bytearray()
    normals = bytearray()
    uvs = bytearray()
    indices = bytearray()
    for y in range(width):
        for x in range(width):
            fx = x/(width-1)
            fy = y/(width-1)
            positions.extend(struct.pack("<fff", float(fx), float(fy), 0.0))
            normals.extend(struct.pack("<fff", 0.0, 0.0, 1.0))
            uvs.extend(struct.pack("<ff", float(fx), float(fy)))
    for y in range(width-1):
        for x in range(width-1):
            a = y*width+x
            b = a+1
            c = a+width
            d = c+1
            indices.extend(struct.pack("<6I",a,b,d,a,d,c))
    assert (len(indices)//4)//3 == 2*(width-1)**2
    p = chunk(positions,34962)
    n = chunk(normals,34962)
    t = chunk(uvs,34962)
    i = chunk(indices,34963)
    count=width*width
    gltf = {
      "asset":{"version":"2.0","generator":"XZIEL procedural no-decimation CI"},
      "buffers":[{"byteLength":len(data)}],
      "bufferViews":views,
      "accessors":[
         {"bufferView":p,"componentType":5126,"count":count,"type":"VEC3",
          "min":[0,0,0],"max":[1,1,0]},
         {"bufferView":n,"componentType":5126,"count":count,"type":"VEC3"},
         {"bufferView":t,"componentType":5126,"count":count,"type":"VEC2"},
         {"bufferView":i,"componentType":5125,"count":6*(width-1)**2,"type":"SCALAR"}
      ],
      "materials":[{"name":"keep-all-polygons",
                    "pbrMetallicRoughness":{"baseColorFactor":[0.8,0.8,0.9,1.0],
                                             "metallicFactor":0.4,"roughnessFactor":0.3}}],
      "meshes":[{"name":"highpoly","primitives":[{"attributes":{"POSITION":0,"NORMAL":1,"TEXCOORD_0":2},
                                                     "indices":3,"material":0}]}],
      "nodes":[{"mesh":0,"name":"hires_geom"}],
      "scenes":[{"nodes":[0]}],"scene":0
    }
    json_blob=json.dumps(gltf,separators=(",",":")).encode("utf-8")
    json_blob += b" "*((-len(json_blob))%4)
    data.extend(b"\x00"*((-len(data))%4))
    payload=struct.pack("<II",len(json_blob),0x4E4F534A)+json_blob
    payload+=struct.pack("<II",len(data),0x004E4942)+data
    path.write_bytes(struct.pack("<4sII",b"glTF",2,12+len(payload))+payload)
    return 2*(width-1)**2
if __name__=="__main__":
    output=Path("work/Synthetic20K.glb")
    output.parent.mkdir(parents=True,exist_ok=True)
    print(f"Generated {make_dense_glb(output)} indexed triangles at {output}")
