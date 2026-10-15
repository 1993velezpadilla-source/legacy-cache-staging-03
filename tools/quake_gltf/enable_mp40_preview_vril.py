#!/usr/bin/env python3
"""CI-only: enable IQM sidecar graphics on a disposable Android Vril clone."""
import sys
from pathlib import Path

def main(root, original_hands=False):
    path=Path(root)/"source/platform/sdl/gl/gl_xziel_iqm_viewmodel.c"
    before='{"xziel_iqm_viewmodels", "0", true}'
    after='{"xziel_iqm_viewmodels", "1", true}'
    txt=path.read_text()
    if after not in txt:
        if txt.count(before)!=1:
            raise RuntimeError("Unexpected Vril IQM cvar declaration")
        path.write_text(txt.replace(before,after,1))
    if original_hands:
        text=path.read_text()
        hand_off='{"xziel_iqm_original_hands", "0", true}'
        hand_on='{"xziel_iqm_original_hands", "1", true}'
        if hand_on not in text:
            if text.count(hand_off)!=1:
                raise RuntimeError("Authentic hands cvar was not registered")
            path.write_text(text.replace(hand_off,hand_on,1))
        print("MP40_AUTHENTIC_46_FRAME_HANDS_OVERLAY_ENABLED_EXPERIMENT_ONLY")
    print("MP40_IQM_VIEWMODEL_DEFAULT_ON_IN_EXPERIMENTAL_BUILD_ONLY")

if __name__=="__main__":
    if len(sys.argv) not in (2,3) or (len(sys.argv)==3 and sys.argv[2]!="--hands-only"):
        raise SystemExit("usage: enable_mp40_preview_vril.py <vril-root> [--hands-only]")
    main(sys.argv[1], len(sys.argv)==3)
