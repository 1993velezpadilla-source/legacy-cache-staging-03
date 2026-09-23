import importlib.util, json, tempfile, unittest
from pathlib import Path
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("scanner", HERE/"detect_and_proxy.py")
scanner=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scanner)

class ScannerContractTests(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(scanner.slug("Heart Lantern!"),"heart_lantern")

    def test_iou_and_nms(self):
        rows=[
            {"box":[0,0,100,100],"score":.9,"label":"bow"},
            {"box":[5,5,95,95],"score":.8,"label":"bow"},
            {"box":[5,5,95,95],"score":.7,"label":"cherry"},
        ]
        out=scanner.nms(rows,.5)
        self.assertEqual(len(out),2)
        self.assertEqual(out[0]["label"],"bow")

    def test_fallback_is_json_safe(self):
        arr=np.zeros((128,128,3),dtype=np.uint8)
        arr[25:95,30:100]=[255,40,180]
        im=Image.fromarray(arr)
        rows=scanner.fallback_saliency(im)
        json.dumps(rows)
        for r in rows:
            self.assertTrue(all(isinstance(v,int) for v in r["box"]))

    def test_proxy_glb_is_nonzero(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"bow.glb"
            scanner.export_proxy(p,"bow",[0,0,100,70])
            self.assertTrue(p.exists())
            self.assertGreater(p.stat().st_size,100)

    def test_grabcut_returns_mask(self):
        arr=np.zeros((128,128,3),dtype=np.uint8)+30
        arr[35:95,35:95]=[250,60,180]
        mask,box=scanner.segment_grabcut(arr,[30,30,100,100])
        self.assertIsNotNone(mask)
        self.assertEqual(mask.shape,(128,128))
        self.assertGreater(mask.sum(),0)

if __name__=="__main__":
    unittest.main(verbosity=2)
