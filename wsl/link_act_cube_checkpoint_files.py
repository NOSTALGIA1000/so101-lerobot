#!/usr/bin/env python3
from pathlib import Path

root = Path("/home/nostalgia/lerobot_outputs/act_cube_v1/checkpoints/020000")
src_dir = root / "pretrained_model"
for src in src_dir.iterdir():
    dst = root / src.name
    if dst.exists() or dst.is_symlink():
        continue
    dst.symlink_to(src)
    print(f"linked {dst} -> {src}")

for p in sorted(root.iterdir()):
    print(("LINK " if p.is_symlink() else "DIR/FILE "), p.name, "->", p.resolve() if p.is_symlink() else "")
