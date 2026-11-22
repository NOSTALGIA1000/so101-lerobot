#!/usr/bin/env python3
"""Detect the white target zone from the raw ZMQ scene camera.

This is a calibration/logging tool only. It does not control the robot.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np
import zmq


def largest_component(mask: np.ndarray):
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if n <= 1:
        return None
    # Ignore background label 0.
    areas = stats[1:, cv2.CC_STAT_AREA]
    idx = int(np.argmax(areas)) + 1
    area = int(stats[idx, cv2.CC_STAT_AREA])
    x = int(stats[idx, cv2.CC_STAT_LEFT])
    y = int(stats[idx, cv2.CC_STAT_TOP])
    w = int(stats[idx, cv2.CC_STAT_WIDTH])
    h = int(stats[idx, cv2.CC_STAT_HEIGHT])
    cx, cy = centroids[idx]
    return {
        "area": area,
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "cx": float(cx),
        "cy": float(cy),
        "label": idx,
    }


def detect_white_target(bgr: np.ndarray, s_max: int, v_min: int, min_area: int, roi: tuple[float, float, float, float] | None = None):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    # OpenCV HSV: H 0..179, S/V 0..255
    mask = ((hsv[:, :, 1] <= s_max) & (hsv[:, :, 2] >= v_min)).astype(np.uint8)
    if roi is not None:
        img_h, img_w = mask.shape[:2]
        x0f, y0f, x1f, y1f = roi
        x0, y0 = int(max(0, min(img_w, x0f * img_w))), int(max(0, min(img_h, y0f * img_h)))
        x1, y1 = int(max(0, min(img_w, x1f * img_w))), int(max(0, min(img_h, y1f * img_h)))
        roi_mask = np.zeros_like(mask)
        roi_mask[y0:y1, x0:x1] = 1
        mask = mask * roi_mask
    # Remove small speckles and bridge target paper regions.
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    comp = largest_component(mask)
    if comp is None or comp["area"] < min_area:
        return None, mask
    img_h, img_w = bgr.shape[:2]
    bbox_area = max(1, comp["w"] * comp["h"])
    fill = comp["area"] / bbox_area
    confidence = min(1.0, comp["area"] / max(1, min_area)) * min(1.0, fill * 2.0)
    comp.update(
        {
            "err_x": comp["cx"] - (img_w - 1) / 2.0,
            "err_y": comp["cy"] - (img_h - 1) / 2.0,
            "img_w": img_w,
            "img_h": img_h,
            "fill_ratio": fill,
            "confidence": confidence,
        }
    )
    return comp, mask


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--address", default="172.28.48.1")
    ap.add_argument("--port", type=int, default=5555)
    ap.add_argument("--camera", default="scene")
    ap.add_argument("--seconds", type=float, default=3.0)
    ap.add_argument("--out-dir", default="/home/nostalgia/lerobot_outputs/rollouts/white_target_debug")
    ap.add_argument("--csv-path", default="/home/nostalgia/lerobot_outputs/rollouts/white_target_debug.csv")
    ap.add_argument("--s-max", type=int, default=70)
    ap.add_argument("--v-min", type=int, default=155)
    ap.add_argument("--min-area", type=int, default=3000)
    ap.add_argument("--save-every", type=int, default=10)
    ap.add_argument("--roi", default="0.35,0.55,0.85,1.0", help="normalized x0,y0,x1,y1 ROI for target search")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = Path(args.csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    ctx = zmq.Context()
    sock = ctx.socket(zmq.SUB)
    sock.setsockopt_string(zmq.SUBSCRIBE, "")
    sock.connect(f"tcp://{args.address}:{args.port}")

    rows = []
    frame_idx = 0
    deadline = time.time() + args.seconds
    recent = deque(maxlen=30)

    try:
        while time.time() < deadline:
            try:
                msg = sock.recv_string(flags=zmq.NOBLOCK)
            except zmq.Again:
                time.sleep(0.01)
                continue
            data = json.loads(msg)
            image_b64 = data.get("images", {}).get(args.camera)
            if not image_b64:
                continue
            arr = np.frombuffer(base64.b64decode(image_b64), np.uint8)
            bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if bgr is None:
                continue
            roi = tuple(float(x) for x in args.roi.split(",")) if args.roi else None
            comp, mask = detect_white_target(bgr, args.s_max, args.v_min, args.min_area, roi=roi)
            now = time.time()
            row = {
                "t_wall": now,
                "frame": frame_idx,
                "camera": args.camera,
                "detected": comp is not None,
                "s_max": args.s_max,
                "v_min": args.v_min,
            }
            if comp:
                row.update(comp)
                recent.append((comp["err_x"], comp["err_y"], comp["confidence"]))
            rows.append(row)
            if frame_idx % max(1, args.save_every) == 0:
                vis = bgr.copy()
                if comp:
                    x, y, w, h = comp["x"], comp["y"], comp["w"], comp["h"]
                    cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.circle(vis, (int(comp["cx"]), int(comp["cy"])), 5, (0, 0, 255), -1)
                    cv2.putText(vis, f"err=({comp['err_x']:.1f},{comp['err_y']:.1f}) conf={comp['confidence']:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                cv2.imwrite(str(out_dir / f"{frame_idx:04d}_{args.camera}_white_target.jpg"), vis)
                cv2.imwrite(str(out_dir / f"{frame_idx:04d}_{args.camera}_mask.png"), mask * 255)
            frame_idx += 1
    finally:
        sock.close(0)
        ctx.term()

    fieldnames = sorted({k for r in rows for k in r.keys()})
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    detected = [r for r in rows if r.get("detected")]
    print(json.dumps({
        "frames": len(rows),
        "detected": len(detected),
        "csv": str(csv_path),
        "out_dir": str(out_dir),
        "recent_mean_err": None if not recent else [
            float(np.mean([x for x, _, _ in recent])),
            float(np.mean([y for _, y, _ in recent])),
            float(np.mean([c for _, _, c in recent])),
        ],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
