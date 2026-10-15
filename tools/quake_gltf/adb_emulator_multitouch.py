#!/usr/bin/env python3
"""Android emulator console multi-pointer proof of ADS + FIRE + RELOAD.

This is a REAL two-slot touchscreen gesture against the running APK, not an
in-game debug event or synthetic renderer state. Requires one Android emulator.
The QA job reads Vril logcat afterwards; issuing touches alone never means
reload succeeded. Coordinates are the actual v0.26 2400x1080 HUD coordinates.
No installed APK, engine state or original input configuration is modified.
"""
import argparse
import os
import shutil
import struct
import subprocess
import time
from pathlib import Path

WIDTH, HEIGHT = 2400, 1080
ADS = (1668, 621)
FIRE = (2124, 632)
RELOAD = (1932, 848)


def locate_adb():
    """GitHub Linux runners don't consistently put adb on PATH.

    The native emulator workflow already uses ANDROID_HOME/platform-tools/adb.
    Use that identical executable, never silently shell out to missing "adb".
    """
    for env in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        base = os.environ.get(env)
        if base:
            exe = Path(base) / "platform-tools" / "adb"
            if exe.is_file() and os.access(exe, os.X_OK):
                return str(exe)
    on_path = shutil.which("adb")
    if on_path:
        return on_path
    raise RuntimeError("Android platform-tools adb executable unavailable")


def adb(*args, binary=False):
    p = subprocess.run([locate_adb(), *map(str, args)], capture_output=True,
                       timeout=35, check=True)
    return p.stdout if binary else p.stdout.decode("utf-8", "replace")


def event(*words):
    answer = adb("emu", "event", "send", *words)
    if "KO:" in answer or "ERROR" in answer.upper():
        raise RuntimeError("Emulator refused touchscreen input: " + answer)
    return answer


def down(slot, tracking_id, x, y):
    assert slot in (0, 1) and 0 < x < WIDTH and 0 < y < HEIGHT
    packet = [f"EV_ABS:ABS_MT_SLOT:{slot}",
              f"EV_ABS:ABS_MT_TRACKING_ID:{tracking_id}",
              f"EV_ABS:ABS_MT_POSITION_X:{x}",
              f"EV_ABS:ABS_MT_POSITION_Y:{y}",
              "EV_ABS:ABS_MT_PRESSURE:100"]
    if slot == 0:
        packet += ["EV_KEY:BTN_TOUCH:1"]
    return event(*packet, "EV_SYN:0:0")


def up(slot, last=False):
    packet = [f"EV_ABS:ABS_MT_SLOT:{slot}",
              "EV_ABS:ABS_MT_PRESSURE:0",
              "EV_ABS:ABS_MT_TRACKING_ID:-1"]
    if last:
        packet.append("EV_KEY:BTN_TOUCH:0")
    return event(*packet, "EV_SYN:0:0")


def screenshot(path):
    data = adb("exec-out", "screencap", "-p", binary=True)
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("No Android PNG screenshot")
    size = struct.unpack_from(">II", data, 16)
    if size != (WIDTH, HEIGHT):
        raise RuntimeError(f"Wrong Android viewport {size}; refusing stale HUD coordinates")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    print("REAL_ANDROID_MULTITOUCH_SCREENSHOT", path, *size, len(data), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    devices = [row.split()[0] for row in adb("devices").splitlines()[1:]
               if row.strip().endswith("\tdevice")]
    if len(devices) != 1 or not devices[0].startswith("emulator-"):
        raise RuntimeError("Requires EXACTLY ONE working Android emulator")
    print("HARDWARE_MULTITOUCH_ADS_FIRE_RELOAD", devices[0],
          "adb=", locate_adb(), flush=True)
    held_ads = held_other = False
    try:
        down(0, 91, *ADS)
        held_ads = True
        time.sleep(1.3)
        screenshot(args.out / "04-real-ads-multitouch-held.png")
        down(1, 92, *FIRE)
        held_other = True
        time.sleep(0.70)
        up(1)
        held_other = False
        time.sleep(0.20)
        down(1, 93, *RELOAD)
        held_other = True
        time.sleep(0.12)
        up(1)
        held_other = False
        time.sleep(0.25)
        screenshot(args.out / "05-real-ads-plus-reload-extract.png")
        time.sleep(0.63)
        screenshot(args.out / "06-real-ads-plus-reload-reinsert.png")
        print("REAL_EMULATOR_ADS_HELD_DURING_FIRE_AND_RELOAD_INPUT_DISPATCHED", flush=True)
    finally:
        if held_other:
            up(1)
        if held_ads:
            up(0, last=True)


if __name__ == "__main__":
    main()
