import json
import struct
import tempfile
import unittest
from pathlib import Path
from preflight import inspect, parse_glb

def make_glb(doc):
    blob = json.dumps(doc).encode("utf8")
    blob += b" " * ((-len(blob)) % 4)
    body = struct.pack("<II", len(blob), 0x4E4F534A) + blob
    return struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body

class PreflightTests(unittest.TestCase):
    def test_valid_glb_and_reflection(self):
        doc = {"asset": {"version": "2.0"}, "accessors": [{"count": 6}],
               "meshes": [{"primitives": [{"indices": 0, "attributes": {"POSITION": 0, "NORMAL": 0, "TEXCOORD_0": 0}}]}],
               "nodes": [{"mesh": 0, "scale": [-1,1,1]}],
               "skins": [{"joints": [0]}], "animations": [{"name": "reload"}]}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "weapon.glb"
            p.write_bytes(make_glb(doc))
            model, bin_size = parse_glb(p)
            result = inspect(model, bin_size)
            self.assertEqual(result["triangles"], 2)
            self.assertEqual(result["animations"], ["reload"])
            self.assertEqual(result["local_mirrored_nodes"], [0])

    def test_bad_length(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.glb"
            p.write_bytes(make_glb({"asset": {"version": "2.0"}}) + b"x")
            with self.assertRaises(ValueError):
                parse_glb(p)

if __name__ == "__main__":
    unittest.main()
