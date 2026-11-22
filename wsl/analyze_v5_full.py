#!/usr/bin/env python3
"""Print full rollout joint trajectory (decimated) + clamp-style extreme moves."""
import csv
import sys
from pathlib import Path

csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "lerobot_outputs" / "rollouts" / "v5_050000_pure_v5_50k.csv"
rows = list(csv.DictReader(open(csv_path)))
def col(name): return [float(r[name]) for r in rows]

gripper, sl, ef, wf, sp, wr = (col("gripper.pos"), col("shoulder_lift.pos"), col("elbow_flex.pos"),
                               col("wrist_flex.pos"), col("shoulder_pan.pos"), col("wrist_roll.pos"))
n = len(rows)
print(f"frames={n} ({(n/30):.1f}s)  GR range=({min(gripper):.1f},{max(gripper):.1f})")

# per-frame relative magnitude (approx what max_relative_target clamps on)
print("\n idx   GR     SL      EF      WF      SP      WR")
for i in range(0, n, 15):
    print(f"{i:4d} {gripper[i]:6.1f} {sl[i]:7.1f} {ef[i]:7.1f} {wf[i]:7.1f} {sp[i]:6.1f} {wr[i]:6.1f}")

# where does GR reopen (gripper lost?) or stay closed
closed = [i for i, g in enumerate(gripper) if g < 3]
if closed:
    runs = []
    s = p = closed[0]
    for i in closed[1:]:
        if i == p + 1: p = i
        else: runs.append((s, p)); s = p = i
    runs.append((s, p))
    print("\nclosed runs (GR<3):", runs)
