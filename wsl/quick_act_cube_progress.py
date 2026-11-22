#!/usr/bin/env python3
import re
from pathlib import Path

log = Path("/home/nostalgia/lerobot_outputs/act_cube_v1.resume_20260722.log")
ckpt_dir = Path("/home/nostalgia/lerobot_outputs/act_cube_v1/checkpoints")

print("CHECKPOINTS")
if ckpt_dir.exists():
    names = sorted(p.name for p in ckpt_dir.iterdir() if p.is_dir() and p.name.isdigit())
    print(" ".join(names))
    last = ckpt_dir / "last"
    if last.is_symlink():
        print(f"last -> {last.readlink()}")

print("LOG")
if not log.exists():
    print("missing")
    raise SystemExit

data = log.read_bytes()[-2_000_000:].decode("utf-8", "replace")
info_lines = [ln for ln in data.splitlines() if " ot_train.py:609 step:" in ln or "eval_loss=" in ln]
if info_lines:
    for ln in info_lines[-8:]:
        print(ln)

progress_matches = re.findall(r"Training:\s+(\d+)%.*?\|\s*(\d+)/30000.*?([0-9.]+)step/s", data)
if progress_matches:
    pct, done, speed = progress_matches[-1]
    done = int(done)
    total_global = 20000 + done
    remaining = 30000 - done
    speed_f = float(speed)
    eta_min = remaining / speed_f / 60 if speed_f > 0 else None
    print(f"resume_done={done}/30000")
    print(f"global_step_est={total_global}/50000")
    print(f"resume_pct={pct}%")
    print(f"speed_step_s={speed}")
    if eta_min is not None:
        print(f"eta_min={eta_min:.1f}")
