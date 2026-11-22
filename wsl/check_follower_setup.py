#!/usr/bin/env python3
from pathlib import Path
import glob
import subprocess

print("DEVICES")
for pattern in ("/dev/ttyUSB*", "/dev/ttyACM*"):
    for name in sorted(glob.glob(pattern)):
        p = Path(name)
        try:
            print(name, oct(p.stat().st_mode & 0o777))
        except FileNotFoundError:
            pass

print("USB")
try:
    out = subprocess.check_output(["lsusb"], text=True, stderr=subprocess.DEVNULL)
    for line in out.splitlines():
        low = line.lower()
        if "1a86" in low or "ch34" in low or "serial" in low:
            print(line)
except Exception as exc:
    print(f"lsusb_unavailable={exc}")

print("CKPT")
ckpt = Path("/home/nostalgia/lerobot_outputs/act_cube_v1/checkpoints/050000/pretrained_model")
print("ckpt_050000_ok" if ckpt.is_dir() else "ckpt_missing")

print("CALIB")
count = 0
for root in [
    Path("/home/nostalgia/.cache"),
    Path("/home/nostalgia/lerobot_workspace"),
    Path("/home/nostalgia/Downloads"),
    Path("/home/nostalgia/下载"),
    Path("/home/nostalgia"),
]:
    if not root.exists():
        continue
    for p in root.rglob("*R12260101*"):
        if "calib" in str(p).lower() or "calibration" in str(p).lower():
            print(p)
            count += 1
            if count >= 20:
                raise SystemExit
