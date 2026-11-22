#!/usr/bin/env python3
"""Save raw frames directly from the Windows ZMQ camera bridge.

This bypasses LeRobot obs preprocessing so cube-center detection can be
calibrated on the actual camera images.
"""

from __future__ import annotations

import argparse
import base64
import json
import time
from pathlib import Path

import zmq


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", default="172.28.48.1")
    parser.add_argument("--port", type=int, default=5555)
    parser.add_argument("--out-dir", default="/home/nostalgia/lerobot_outputs/rollouts/raw_camera_frames")
    parser.add_argument("--timeout-sec", type=float, default=5.0)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ctx = zmq.Context()
    sock = ctx.socket(zmq.SUB)
    sock.setsockopt_string(zmq.SUBSCRIBE, "")
    sock.setsockopt(zmq.RCVHWM, 2)
    sock.connect(f"tcp://{args.address}:{args.port}")

    deadline = time.time() + args.timeout_sec
    latest: dict[str, str] = {}
    timestamps: dict[str, float] = {}

    try:
        while time.time() < deadline:
            try:
                msg = sock.recv_string(flags=zmq.NOBLOCK)
            except zmq.Again:
                time.sleep(0.02)
                continue
            data = json.loads(msg)
            latest.update(data.get("images", {}))
            timestamps.update(data.get("timestamps", {}))
            if "scene" in latest and "wrist" in latest:
                break
    finally:
        sock.close(0)
        ctx.term()

    if not latest:
        raise SystemExit("no camera frames received from ZMQ bridge")

    meta = {}
    for name, image_b64 in latest.items():
        image_bytes = base64.b64decode(image_b64)
        path = out_dir / f"{name}.jpg"
        path.write_bytes(image_bytes)
        meta[name] = {"path": str(path), "timestamp": timestamps.get(name)}

    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
