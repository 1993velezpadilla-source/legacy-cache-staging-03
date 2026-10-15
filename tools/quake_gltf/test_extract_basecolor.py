import base64
import json
import struct
import tempfile
import unittest
from pathlib import Path
from extract_basecolor import extract

PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    "AAAADUlEQVQIHWP4z8DwHwAFgAI/ScL/nwAAAABJRU5ErkJggg=="
)

def glb_doc(doc, binary):
    binary += b"\0"*((-len(binary))%4)
    doc["buffers"]=[{"byteLength":len(binary)}]
    j=json.dumps(doc,separators=(",",":")).encode()
    j+=b" "*((-len(j))%4)
    payload=struct.pack("<II",len(j),0x4E4F534A)+j
    payload+=struct.pack("<II",len(binary),0x004E4942)+binary
    return struct.pack("<4sII",b"glTF",2,12+len(payload))+payload

class TestExtraction(unittest.TestCase):
    def test_preserve_embedded_png_without_reencode(self):
        png=base64.b64decode(PNG_B64)
        doc={
          "asset":{"version":"2.0"},
          "bufferViews":[{"buffer":0,"byteOffset":0,"byteLength":len(png)}],
          "images":[{"bufferView":0,"mimeType":"image/png"}],
          "textures":[{"source":0}],
          "materials":[{"name":"gun.albedo","pbrMetallicRoughness":{"baseColorTexture":{"index":0}}}],
        }
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            src=root/"a.glb"
            src.write_bytes(glb_doc(doc,png))
            result=extract(src,root/"out")
            self.assertEqual((root/"out"/"gun.albedo.png").read_bytes(),png)
            self.assertEqual(result[0]["bytes"],len(png))
            self.assertFalse(result[0]["resolution_changed"])
            with self.assertRaises(FileExistsError):
                extract(src,root/"out")
if __name__ == "__main__":
    unittest.main()
