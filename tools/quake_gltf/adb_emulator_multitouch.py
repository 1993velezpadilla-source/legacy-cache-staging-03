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
import re
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


def touchscreen_axis_limits():
    # Emulator console EV_ABS injection uses LINUX DEVICE coordinates,
    # not landscape screenshots. Our earlier QA accidentally pressed the
    # LEFT JOYSTICK (visible in screenshot 04) instead of ADS, and then
    # asserted the first-person reload was broken. Read real device limits.
    info = adb("shell", "getevent", "-lp")
    for device in re.split(r"(?=add device \d+:)", info):
        if ("ABS_MT_POSITION_X" not in device or
            "ABS_MT_POSITION_Y" not in device or "ABS_MT_SLOT" not in device):
            continue
        limits = {}
        for axis in ("X", "Y"):
            found = re.search(r"ABS_MT_POSITION_"+axis+
                              r"\s*:\s*value\s+-?\d+,\s*min\s+(-?\d+),\s*max\s+(-?\d+)",device)
            if found:
                limits[axis] = tuple(map(int,found.groups()))
        if set(limits)=={"X","Y"} and all(b>a for a,b in limits.values()):
            print("ANDROID_REAL_TOUCH_AXIS_LIMITS",limits,flush=True)
            return limits
    raise RuntimeError("Cannot determine actual emulator touchscreen ABS axes; refusing 2400x1080 blind raw injection")


def map_landscape_to_raw(x,y,limits,rotation):
    if not (0<=x<WIDTH and 0<=y<HEIGHT):
        raise RuntimeError(f"bad Android screen touch {x},{y}")
    nx=x/(WIDTH-1)
    ny=y/(HEIGHT-1)
    if rotation==0: a,b=nx,ny
    elif rotation==90: a,b=ny,1-nx
    elif rotation==180: a,b=1-nx,1-ny
    elif rotation==270: a,b=1-ny,nx
    else: raise RuntimeError("rotation invalid")
    x0,x1=limits["X"];y0,y1=limits["Y"]
    return (round(x0+(x1-x0)*a),round(y0+(y1-y0)*b))


def down(slot,tracking_id,x,y,limits,rotation):
    assert slot in (0,1)
    raw_x,raw_y=map_landscape_to_raw(x,y,limits,rotation)
    print("ACTUAL_ANDROID_HUD_TO_RAW_TOUCH",slot,rotation,(x,y),(raw_x,raw_y),flush=True)
    packet = [f"EV_ABS:ABS_MT_SLOT:{slot}",
              f"EV_ABS:ABS_MT_TRACKING_ID:{tracking_id}",
              f"EV_ABS:ABS_MT_POSITION_X:{raw_x}",
              f"EV_ABS:ABS_MT_POSITION_Y:{raw_y}",
              "EV_ABS:ABS_MT_PRESSURE:100"]
    if slot == 0:
        packet += ["EV_KEY:BTN_TOUCH:1"]
    return event(*packet, "EV_SYN:0:0")


def gesture_log_count():
    return adb("logcat","-d","-s","XZIEL_IQM:I","*:S").count("ADS_FRESH_TOUCH_GESTURE_HELD")


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
    limits=touchscreen_axis_limits()
    (args.out/"touch-axis-limits.txt").write_text(str(limits))
    held_ads=held_other=False
    angle=None
    try:
        # Device coordinates may be portrait while the APK is landscape.
        # PROBE the actual Vril ADS interpolator with the real touch event
        # after EACH orientation. This is a fail-closed runtime assertion;
        # merely sending plausible EV_ABS packets is not proof of ADS.
        for candidate in (90,270,0,180):
            previous=gesture_log_count()
            down(0,91,*ADS,limits,candidate)
            held_ads=True
            time.sleep(1.65)
            current=gesture_log_count()
            if current>previous:
                angle=candidate
                print("ANDROID_REAL_MULTITOUCH_ORIENTATION_VERIFIED",angle,
                      "new_ads_events",current-previous,flush=True)
                break
            up(0,last=True)
            held_ads=False
            time.sleep(0.45)
        if angle is None:
            screenshot(args.out/"04-ads-touch-mapping-FAILED.png")
            raise RuntimeError("ADH_TOUCH_MAPPING_RED: No raw axis orientation triggered real ADS; do not claim multi-touch works.")
        screenshot(args.out / "04-real-ads-multitouch-held.png")
        down(1,92,*FIRE,limits,angle)
        held_other=True
        time.sleep(0.60)
        up(1)
        held_other=False
        time.sleep(0.12)
        down(1,93,*RELOAD,limits,angle)
        held_other=True
        time.sleep(0.12)
        up(1)
        held_other=False
        time.sleep(0.22)
        screenshot(args.out/"05-real-ads-plus-reload-extract.png")
        time.sleep(0.6)
        screenshot(args.out/"06-real-ads-plus-reload-reinsert.png")
        print("REAL_ANDROID_MULTITOUCH_ADS_VERIFIED_FIRE_RELOAD_INPUT_SENT",flush=True)
    finally:
        if held_other:up(1)
        if held_ads:up(0,last=True)


if __name__ == "__main__":
    main()
