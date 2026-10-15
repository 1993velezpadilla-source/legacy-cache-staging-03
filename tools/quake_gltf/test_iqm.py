import struct
import tempfile
import unittest
from pathlib import Path
from inspect_iqm import parse_iqm

def make_iqm(ntriangles=1):
    head = [2, 136 + 12*ntriangles, 0, 1, 124, 0,0,0,0,0,
            ntriangles,136,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    # 124 byte header + text byte + padding (11 bytes) + N triangles
    return struct.pack("<16s27I",b"INTERQUAKEMODEL\x00",*head) + b"\x00" + (b"\x00"*11) + (b"\x00"*12*ntriangles)
class IQMTests(unittest.TestCase):
    def test_iqm_header(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.iqm"
            p.write_bytes(make_iqm())
            self.assertEqual(parse_iqm(p)["triangles"],1)
    def test_truncated_triangle(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.iqm"
            p.write_bytes(make_iqm()[:-1])
            with self.assertRaises(ValueError):
                parse_iqm(p)
if __name__ == "__main__":
    unittest.main()
