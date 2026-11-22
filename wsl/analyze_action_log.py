#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/nostalgia/lerobot_outputs/rollouts/v2_050000_cube_10s_actionlog.csv")
    rows = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: float(v) for k, v in row.items()})

    print(f"csv={path}")
    print(f"rows={len(rows)}")
    if not rows:
        return
    keys = list(rows[0].keys())
    action_keys = [k for k in keys if k != "t_wall"]
    print("ordered_keys=" + ",".join(action_keys))

    t0 = rows[0]["t_wall"]
    for row in rows:
        row["t"] = row["t_wall"] - t0

    print("\n[stats]")
    for key in action_keys:
        vals = [row[key] for row in rows]
        print(
            f"{key}: start={vals[0]:.3f}, end={vals[-1]:.3f}, "
            f"min={min(vals):.3f}, max={max(vals):.3f}"
        )

    print("\n[gripper threshold crossings]")
    for threshold in [50, 35, 25, 15, 10, 5]:
        hit = next((row for row in rows if row["gripper.pos"] < threshold), None)
        if not hit:
            print(f"gripper<{threshold}: never")
            continue
        vals = ", ".join(f"{key}={hit[key]:.3f}" for key in action_keys)
        print(f"gripper<{threshold}: t={hit['t']:.3f}, {vals}")

    print("\n[nearest 1s samples]")
    duration = int(rows[-1]["t"]) + 1
    for sec in range(duration + 1):
        row = min(rows, key=lambda x: abs(x["t"] - sec))
        vals = ", ".join(f"{key}={row[key]:.2f}" for key in action_keys)
        print(f"t={row['t']:.2f}, {vals}")


if __name__ == "__main__":
    main()
