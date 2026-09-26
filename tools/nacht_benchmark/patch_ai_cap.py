#!/usr/bin/env python3
"""Prepare an Xziel/Vril checkout for a Nacht AI-cap stress build.

This is benchmark-only tooling. It changes only the compile-time MAX_AI_COUNT
define in android/jni/src/Android.mk and refuses unsupported caps.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ALLOWED_CAPS = (24, 48, 96)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("xziel_root", type=Path)
    ap.add_argument("--cap", type=int, required=True, choices=ALLOWED_CAPS)
    args = ap.parse_args()

    mk = args.xziel_root / "android" / "jni" / "src" / "Android.mk"
    if not mk.is_file():
        raise SystemExit(f"missing Android.mk: {mk}")

    text = mk.read_text(encoding="utf-8")
    matches = re.findall(r"-DMAX_AI_COUNT=(\d+)", text)
    if len(matches) != 1:
        raise SystemExit(
            f"expected exactly one MAX_AI_COUNT define in {mk}, found {len(matches)}"
        )

    old = int(matches[0])
    if old not in ALLOWED_CAPS:
        raise SystemExit(
            f"refusing unexpected existing MAX_AI_COUNT={old}; "
            f"expected one of {ALLOWED_CAPS}"
        )

    new = re.sub(
        r"-DMAX_AI_COUNT=\d+",
        f"-DMAX_AI_COUNT={args.cap}",
        text,
        count=1,
    )
    mk.write_text(new, encoding="utf-8")
    print(f"Nacht benchmark AI cap: {old} -> {args.cap}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
