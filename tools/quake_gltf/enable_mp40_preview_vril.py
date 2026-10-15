#!/usr/bin/env python3
"""CI-only: enable IQM sidecar graphics on a disposable Android Vril clone."""
import sys
from pathlib import Path

def main(root):
    path=Path(root)/"source/platform/sdl/gl/gl_xziel_iqm_viewmodel.c"
    before='{"xziel_iqm_viewmodels", "0", true}'
    after='{"xziel_iqm_viewmodels", "1", true}'
    txt=path.read_text()
    if after not in txt:
        if txt.count(before)!=1:
            raise RuntimeError("Unexpected Vril IQM cvar declaration")
        path.write_text(txt.replace(before,after,1))
    print("MP40_IQM_VIEWMODEL_DEFAULT_ON_IN_EXPERIMENTAL_BUILD_ONLY")

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: enable_mp40_preview_vril.py <vril-root>")
    main(sys.argv[1])
