#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
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
    parser.add_argument("--joint", default="wrist_roll")
    parser.add_argument("--delta", type=float, default=23.0)
    parser.add_argument("--hold", type=float, default=1.0)
    parser.add_argument(
        "--calibration",
        default="/home/nostalgia/.cache/huggingface/lerobot/calibration/robots/so_follower/R12260101.json",
    )
    args = parser.parse_args()

    calibration = json.loads(Path(args.calibration).read_text())
    bus = FeetechMotorsBus(args.port, MOTORS, calibration=calibration)
    try:
        bus.connect(handshake=True)
        before = bus.sync_read("Present_Position", normalize=False)
        print(f"before={before}")

        target = dict(before)
        target[args.joint] = float(target[args.joint]) + args.delta
        print(f"target={target}")
        bus.sync_write("Goal_Position", target)
        time.sleep(args.hold)

        mid = bus.sync_read("Present_Position", normalize=False)
        print(f"mid={mid}")

        bus.sync_write("Goal_Position", before)
        time.sleep(args.hold)

        after = bus.sync_read("Present_Position", normalize=False)
        print(f"after={after}")
    finally:
        if bus.is_connected:
            bus.disconnect(disable_torque=False)


if __name__ == "__main__":
    main()
