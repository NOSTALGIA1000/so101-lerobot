#!/usr/bin/env python3
"""Analyze a rollout action CSV: find gripper-close, print joint trajectory around it."""
import csv
import sys
from pathlib import Path

csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "lerobot_outputs" / "rollouts" / "v5_050000_pure_v5_50k.csv"

rows = list(csv.DictReader(open(csv_path)))
def col(name):
    return [float(r[name]) for r in rows]

gripper, sl, ef, wf, sp = col("gripper.pos"), col("shoulder_lift.pos"), col("elbow_flex.pos"), col("wrist_flex.pos"), col("shoulder_pan.pos")

print(f"frames={len(rows)}  gripper range=({min(gripper):.1f},{max(gripper):.1f})")

# gripper is open high / closed low. Find first sustained close (drop below midpoint after frame 50)
hi = max(gripper); lo = min(gripper); mid = (hi + lo) / 2
close_i = None
for i, g in enumerate(gripper):
    if i > 50 and g < mid:
        close_i = i
        break
print(f"first close frame={close_i}  (GR={gripper[close_i] if close_i else '-'})")

if close_i:
    start = max(0, close_i - 2)
    end = min(len(rows), close_i + 30)
    print("  idx    GR     SL      EF      WF      SP")
    for i in range(start, end, 1):
        print(f"{i:5d} {gripper[i]:6.1f} {sl[i]:7.1f} {ef[i]:7.1f} {wf[i]:7.1f} {sp[i]:6.1f}")
    # post-grasp direction: first 15 frames after close
    if close_i + 15 < len(rows):
        dSL = sl[close_i+15] - sl[close_i]
        dEF = ef[close_i+15] - ef[close_i]
        dWF = wf[close_i+15] - wf[close_i]
        print(f"post-grasp 15f deltas: dSL={dSL:+.1f} dEF={dEF:+.1f} dWF={dWF:+.1f}")
        print(f"  SL{dSL:+} = {'抬' if dSL > 0 else '下压'}  EF{dEF:+} = {'抬' if dEF > 0 else '放低'}  WF{dWF:+} = {'低头' if dWF < 0 else '仰头'}")
