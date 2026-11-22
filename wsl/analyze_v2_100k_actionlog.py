from __future__ import annotations

import csv
import math
from pathlib import Path

path = Path("/home/nostalgia/lerobot_outputs/rollouts/v2_100000_cube_10s_actionlog_original.csv")
rows = list(csv.DictReader(path.open()))
keys = ["shoulder_lift.pos", "elbow_flex.pos", "wrist_flex.pos", "gripper.pos"]

def f(row, key):
    return float(row[key])

t0 = float(rows[0]["t_wall"])
print("file", path)
print("rows", len(rows), "duration_s", float(rows[-1]["t_wall"]) - t0)

for key in keys:
    vals = [f(r, key) for r in rows]
    print(
        key,
        "min", round(min(vals), 3),
        "max", round(max(vals), 3),
        "first", round(vals[0], 3),
        "last", round(vals[-1], 3),
    )

print("\nSAMPLES")
n = len(rows)
for idx in [0, int(n*0.1), int(n*0.2), int(n*0.3), int(n*0.4), int(n*0.5), int(n*0.6), int(n*0.7), int(n*0.8), int(n*0.9), n-1]:
    r = rows[idx]
    print(
        idx,
        "dt", round(float(r["t_wall"]) - t0, 3),
        "sl", round(f(r, "shoulder_lift.pos"), 3),
        "ef", round(f(r, "elbow_flex.pos"), 3),
        "wf", round(f(r, "wrist_flex.pos"), 3),
        "g", round(f(r, "gripper.pos"), 3),
    )

def count_trigger(name, predicate):
    hits = []
    for i, r in enumerate(rows):
        sl = f(r, "shoulder_lift.pos")
        ef = f(r, "elbow_flex.pos")
        wf = f(r, "wrist_flex.pos")
        g = f(r, "gripper.pos")
        if predicate(sl, ef, wf, g):
            hits.append((i, float(r["t_wall"]) - t0, sl, ef, wf, g))
    print("\nTRIGGER", name, "hits", len(hits), "/", len(rows))
    if hits:
        print("first", tuple(round(x, 3) if isinstance(x, float) else x for x in hits[0]))
        print("last ", tuple(round(x, 3) if isinstance(x, float) else x for x in hits[-1]))
        for h in hits[:: max(1, len(hits)//5)][:6]:
            print("sample", tuple(round(x, 3) if isinstance(x, float) else x for x in h))

count_trigger(
    "old: sl>20 ef<-30 wf>80",
    lambda sl, ef, wf, g: sl > 20 and ef < -30 and wf > 80,
)
count_trigger(
    "narrowA: sl>35 ef<-50 wf>95",
    lambda sl, ef, wf, g: sl > 35 and ef < -50 and wf > 95,
)
count_trigger(
    "narrowB: sl>38 ef<-53 wf>98",
    lambda sl, ef, wf, g: sl > 38 and ef < -53 and wf > 98,
)

# Approximate stability: moving average absolute delta over last 10 frames.
print("\nSTABILITY CANDIDATES")
for i in range(10, len(rows)):
    deltas = []
    for key in ["shoulder_lift.pos", "elbow_flex.pos", "wrist_flex.pos"]:
        vals = [f(rows[j], key) for j in range(i - 10, i + 1)]
        deltas.append(sum(abs(vals[k] - vals[k-1]) for k in range(1, len(vals))) / 10.0)
    sl, ef, wf, g = [f(rows[i], k) for k in ["shoulder_lift.pos", "elbow_flex.pos", "wrist_flex.pos", "gripper.pos"]]
    if sl > 35 and ef < -50 and wf > 95 and max(deltas) < 1.2:
        print(
            "first_stable_grasp_like",
            i,
            "dt", round(float(rows[i]["t_wall"]) - t0, 3),
            "sl", round(sl, 3),
            "ef", round(ef, 3),
            "wf", round(wf, 3),
            "g", round(g, 3),
            "mean_abs_delta", [round(d, 3) for d in deltas],
        )
        break
