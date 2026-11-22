#!/usr/bin/env python3
"""Read-only SO-ARM101 follower communication check.

This opens the Feetech serial bus, verifies the expected motor IDs answer,
reads Present_Position once, and closes the serial port without writing motor
configuration, goal position, or torque state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus


MOTORS = {
    "shoulder_pan": Motor(1, "sts3215", MotorNormMode.DEGREES),
    "shoulder_lift": Motor(2, "sts3215", MotorNormMode.DEGREES),
    "elbow_flex": Motor(3, "sts3215", MotorNormMode.DEGREES),
    "wrist_flex": Motor(4, "sts3215", MotorNormMode.DEGREES),
    "wrist_roll": Motor(5, "sts3215", MotorNormMode.DEGREES),
    "gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/ttyACM0")
    parser.add_argument(
        "--calibration",
        default="/home/nostalgia/.cache/huggingface/lerobot/calibration/robots/so_follower/R12260101.json",
    )
    args = parser.parse_args()

    calibration_path = Path(args.calibration)
    if not calibration_path.exists():
        raise FileNotFoundError(calibration_path)

    calibration = json.loads(calibration_path.read_text())
    missing = sorted(set(MOTORS) - set(calibration))
    extra = sorted(set(calibration) - set(MOTORS))
    print(f"calibration={calibration_path}")
    print(f"calibration_motors={sorted(calibration)}")
    if missing or extra:
        raise RuntimeError(f"Calibration mismatch: missing={missing}, extra={extra}")

    bus = FeetechMotorsBus(args.port, MOTORS, calibration=calibration)
    try:
        bus.connect(handshake=True)
        positions = bus.sync_read("Present_Position", normalize=False)
        print(f"port={args.port}")
        print(f"positions={positions}")
    finally:
        if bus.is_connected:
            bus.disconnect(disable_torque=False)


if __name__ == "__main__":
    main()
