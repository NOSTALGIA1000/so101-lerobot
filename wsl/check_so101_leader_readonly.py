#!/usr/bin/env python3
"""Read-only SO101 leader check.

This connects to a SO101 leader, reads one action frame, prints the six joint
positions, and disconnects. It does not command the follower.
"""

from __future__ import annotations

import argparse

from lerobot.teleoperators.so_leader.config_so_leader import SOLeaderTeleopConfig
from lerobot.teleoperators.so_leader.so_leader import SO101Leader


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--id", required=True)
    args = parser.parse_args()

    teleop = SO101Leader(SOLeaderTeleopConfig(port=args.port, id=args.id))
    try:
        teleop.connect()
        action = teleop.get_action()
        print(f"port={args.port}")
        print(f"id={args.id}")
        print(f"action={action}")
    finally:
        if teleop.is_connected:
            teleop.disconnect()


if __name__ == "__main__":
    main()

