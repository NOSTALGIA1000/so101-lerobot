#!/usr/bin/env python3
"""Log scene-camera image-space place error for SO-ARM101.

This is a research/calibration tool only. It does not command the robot.

It detects:
  1. White target zone: low saturation + high value inside a table ROI.
  2. Cube candidate: saturated non-white object inside a cube ROI.

Then it logs:
  dx = target_cx - cube_cx
  dy = target_cy - cube_cy

The result is intended for validating whether a future place servo can use
scene-camera OpenCV feedback instead of fixed joint-space macros.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import time
from pathlib import Path

import cv2
import numpy as np
import zmq


def parse_roi(text: str | None) -> tuple[float, float, float, float] | None:
    if not text:
        return None
    vals = tuple(float(x) for x in text.split(","))
    if len(vals) != 4:
        raise ValueError(f"ROI must be x0,y0,x1,y1, got {text!r}")
    return vals


def apply_roi(mask: np.ndarray, roi: tuple[float, float, float, float] | None) -> np.ndarray:
    if roi is None:
        return mask
    h, w = mask.shape[:2]
    x0f, y0f, x1f, y1f = roi
    x0 = int(max(0, min(w, x0f * w)))
    y0 = int(max(0, min(h, y0f * h)))
    x1 = int(max(0, min(w, x1f * w)))
    y1 = int(max(0, min(h, y1f * h)))
    out = np.zeros_like(mask)
    out[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
    return out


def largest_component(mask: np.ndarray, min_area: int) -> dict | None:
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if n <= 1:
        return None
    areas = stats[1:, cv2.CC_STAT_AREA]
    idx = int(np.argmax(areas)) + 1
    area = int(stats[idx, cv2.CC_STAT_AREA])
    if area < min_area:
        return None
    x = int(stats[idx, cv2.CC_STAT_LEFT])
    y = int(stats[idx, cv2.CC_STAT_TOP])
    w = int(stats[idx, cv2.CC_STAT_WIDTH])
    h = int(stats[idx, cv2.CC_STAT_HEIGHT])
    cx, cy = centroids[idx]
    return {"area": area, "x": x, "y": y, "w": w, "h": h, "cx": float(cx), "cy": float(cy)}


def clean_mask(mask: np.ndarray, kernel_size: int) -> np.ndarray:
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def detect_white_target(
    bgr: np.ndarray,
    *,
    roi: tuple[float, float, float, float] | None,
    s_max: int,
    v_min: int,
    min_area: int,
) -> tuple[dict | None, np.ndarray]:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = ((hsv[:, :, 1] <= s_max) & (hsv[:, :, 2] >= v_min)).astype(np.uint8)
    mask = apply_roi(mask, roi)
    mask = clean_mask(mask, 5)
    return largest_component(mask, min_area), mask


def detect_cube_candidate(
    bgr: np.ndarray,
    *,
    roi: tuple[float, float, float, float] | None,
    mode: str,
    s_min: int,
    v_min: int,
    min_area: int,
    max_area: int,
) -> tuple[dict | None, np.ndarray]:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    if mode == "purple":
        # Purple cube on blue table. Keep hue-specific threshold to avoid
        # detecting the whole saturated blue tabletop.
        h = hsv[:, :, 0]
        mask = ((h >= 120) & (h <= 170) & (hsv[:, :, 1] >= s_min) & (hsv[:, :, 2] >= v_min)).astype(np.uint8)
    elif mode == "red":
        h = hsv[:, :, 0]
        mask = (((h <= 10) | (h >= 170)) & (hsv[:, :, 1] >= s_min) & (hsv[:, :, 2] >= v_min)).astype(np.uint8)
    else:
        # Generic colored object detector. Useful only when the table is not
        # strongly saturated.
        mask = ((hsv[:, :, 1] >= s_min) & (hsv[:, :, 2] >= v_min)).astype(np.uint8)
    mask = apply_roi(mask, roi)
    mask = clean_mask(mask, 3)
    comp = largest_component(mask, min_area)
    if comp and comp["area"] > max_area:
        return None, mask
    return comp, mask


def draw_detection(vis: np.ndarray, comp: dict | None, color: tuple[int, int, int], label: str) -> None:
    if not comp:
        return
    x, y, w, h = comp["x"], comp["y"], comp["w"], comp["h"]
    cx, cy = int(comp["cx"]), int(comp["cy"])
    cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)
    cv2.circle(vis, (cx, cy), 4, color, -1)
    cv2.putText(vis, label, (x, max(20, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--address", default="172.28.48.1")
    ap.add_argument("--port", type=int, default=5555)
    ap.add_argument("--camera", default="scene")
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--out-dir", default="/home/nostalgia/lerobot_outputs/rollouts/scene_place_error_debug")
    ap.add_argument("--csv-path", default="/home/nostalgia/lerobot_outputs/rollouts/scene_place_error_debug.csv")
    ap.add_argument("--save-every", type=int, default=10)
    ap.add_argument("--target-roi", default="0.35,0.55,0.90,1.0")
    ap.add_argument("--cube-roi", default="0.05,0.30,0.95,0.95")
    ap.add_argument("--cube-mode", choices=["purple", "red", "generic"], default="purple")
    ap.add_argument("--target-s-max", type=int, default=70)
    ap.add_argument("--target-v-min", type=int, default=155)
    ap.add_argument("--target-min-area", type=int, default=3000)
    ap.add_argument("--cube-s-min", type=int, default=50)
    ap.add_argument("--cube-v-min", type=int, default=60)
    ap.add_argument("--cube-min-area", type=int, default=80)
    ap.add_argument("--cube-max-area", type=int, default=12000)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = Path(args.csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    target_roi = parse_roi(args.target_roi)
    cube_roi = parse_roi(args.cube_roi)

    ctx = zmq.Context()
    sock = ctx.socket(zmq.SUB)
    sock.setsockopt_string(zmq.SUBSCRIBE, "")
    sock.setsockopt(zmq.RCVHWM, 2)
    sock.connect(f"tcp://{args.address}:{args.port}")

    rows: list[dict] = []
    frame = 0
    deadline = time.time() + args.seconds

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

            target, target_mask = detect_white_target(
                bgr,
                roi=target_roi,
                s_max=args.target_s_max,
                v_min=args.target_v_min,
                min_area=args.target_min_area,
            )
            cube, cube_mask = detect_cube_candidate(
                bgr,
                roi=cube_roi,
                mode=args.cube_mode,
                s_min=args.cube_s_min,
                v_min=args.cube_v_min,
                min_area=args.cube_min_area,
                max_area=args.cube_max_area,
            )

            row = {
                "t_wall": time.time(),
                "frame": frame,
                "target_detected": target is not None,
                "cube_detected": cube is not None,
            }
            if target:
                row.update({f"target_{k}": v for k, v in target.items()})
            if cube:
                row.update({f"cube_{k}": v for k, v in cube.items()})
            if target and cube:
                row["dx_target_minus_cube"] = target["cx"] - cube["cx"]
                row["dy_target_minus_cube"] = target["cy"] - cube["cy"]
            rows.append(row)

            if frame % max(1, args.save_every) == 0:
                vis = bgr.copy()
                draw_detection(vis, target, (0, 0, 255), "target")
                draw_detection(vis, cube, (0, 255, 0), "cube")
                if target and cube:
                    cv2.line(
                        vis,
                        (int(cube["cx"]), int(cube["cy"])),
                        (int(target["cx"]), int(target["cy"])),
                        (255, 0, 0),
                        2,
                    )
                    cv2.putText(
                        vis,
                        f"dx={row['dx_target_minus_cube']:.1f} dy={row['dy_target_minus_cube']:.1f}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 0, 0),
                        2,
                    )
                cv2.imwrite(str(out_dir / f"{frame:04d}_{args.camera}_place_error.jpg"), vis)
                cv2.imwrite(str(out_dir / f"{frame:04d}_{args.camera}_target_mask.png"), target_mask * 255)
                cv2.imwrite(str(out_dir / f"{frame:04d}_{args.camera}_cube_mask.png"), cube_mask * 255)

            frame += 1
    finally:
        sock.close(0)
        ctx.term()

    fieldnames = sorted({k for r in rows for k in r})
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    valid = [r for r in rows if r.get("target_detected") and r.get("cube_detected")]
    summary = {
        "frames": len(rows),
        "valid_pairs": len(valid),
        "csv": str(csv_path),
        "out_dir": str(out_dir),
        "mean_dx_dy": None
        if not valid
        else [
            float(np.mean([r["dx_target_minus_cube"] for r in valid])),
            float(np.mean([r["dy_target_minus_cube"] for r in valid])),
        ],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
