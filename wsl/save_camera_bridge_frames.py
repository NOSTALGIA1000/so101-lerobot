#!/usr/bin/env python3
from pathlib import Path

import cv2
from lerobot.cameras.zmq import ZMQCamera, ZMQCameraConfig


out_dir = Path("/mnt/c/Users/ASUS/Documents/lerobot/camera_bridge_frames")
out_dir.mkdir(parents=True, exist_ok=True)


def save(name: str) -> None:
    camera = ZMQCamera(
        ZMQCameraConfig(
            server_address="172.28.48.1",
            port=5555,
            camera_name=name,
            width=640,
            height=480,
            fps=30,
            timeout_ms=5000,
        )
    )
    try:
        camera.connect()
        frame = camera.async_read(timeout_ms=5000)
        path = out_dir / f"{name}.jpg"
        cv2.imwrite(str(path), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        print(f"{name}: {frame.shape} -> {path}")
    finally:
        camera.disconnect()


for camera_name in ("wrist", "scene"):
    save(camera_name)
