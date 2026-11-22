"""Grab one frame from the Windows ZMQ camera bridge and save it.

Borrows the SUB protocol from preflight_check.py; decodes the base64 JPEG
that windows_camera_zmq_server.py publishes.

Usage:
    python3 capture_scene_frame.py [--camera scene|wrist] [--out PATH] [--all]
"""
import argparse
import base64
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import zmq

BRIDGE_ADDR = "tcp://172.28.48.1:5555"


def grab_once(camera_names: list[str] | None, timeout_ms: int = 5000):
    """Return {camera_name: decoded BGR ndarray} from one bridge message."""
    ctx = zmq.Context()
    sock = ctx.socket(zmq.SUB)
    sock.setsockopt_string(zmq.SUBSCRIBE, "")
    sock.setsockopt(zmq.RCVTIMEO, timeout_ms)
    try:
        sock.connect(BRIDGE_ADDR)
        msg = sock.recv_string()
        data = json.loads(msg)
        images = data.get("images", {})
        if not images:
            print(f"[FAIL] bridge message has no images: {data.keys()}", file=sys.stderr)
            sys.exit(3)
        out: dict[str, np.ndarray] = {}
        for name, b64 in images.items():
            if camera_names is not None and name not in camera_names:
                continue
            jpg = np.frombuffer(base64.b64decode(b64), dtype=np.uint8)
            frame = cv2.imdecode(jpg, cv2.IMREAD_COLOR)
            if frame is not None:
                out[name] = frame
        return out
    except zmq.ZMQError as e:
        print(f"[FAIL] camera bridge ({BRIDGE_ADDR}): {e}", file=sys.stderr)
        print("  start it on Windows: F:\\CC-project\\lerobot\\start_camera_bridge_two.ps1", file=sys.stderr)
        sys.exit(4)
    finally:
        sock.close()
        ctx.term()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", choices=["scene", "wrist"], default="scene")
    parser.add_argument("--out", default="scene_frame.png", help="output PNG path")
    parser.add_argument("--all", action="store_true", help="save every camera to --out dir")
    args = parser.parse_args()

    frames = grab_once(None if args.all else [args.camera])
    if not frames:
        print(f"[FAIL] no frames for camera '{args.camera}'", file=sys.stderr)
        sys.exit(5)

    if args.all:
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, frame in frames.items():
            path = out_dir / f"{name}.png"
            cv2.imwrite(str(path), frame)
            print(f"[OK] {name} -> {path}  {frame.shape[1]}x{frame.shape[0]}")
    else:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        frame = frames[args.camera]
        cv2.imwrite(str(path), frame)
        print(f"[OK] {args.camera} -> {path}  {frame.shape[1]}x{frame.shape[0]}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        import traceback

        traceback.print_exc()
        raise
