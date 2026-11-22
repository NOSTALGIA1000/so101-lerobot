#!/usr/bin/env python3
"""Read-only bus scan using LeRobot's FeetechMotorsBus.scan_port().
Scans both ports, reports found motor IDs at each baud rate.
Does NOT write IDs. Does NOT reconfigure."""

from lerobot.motors.feetech import FeetechMotorsBus

for port in ["/dev/ttyACM0", "/dev/ttyACM1"]:
    print(f"\n{'='*60}")
    print(f"Scanning {port}...")
    print(f"{'='*60}")
    try:
        result = FeetechMotorsBus.scan_port(port)
        if result:
            print(f"FOUND motors at baud rates:")
            for br, ids in result.items():
                print(f"  {br}: IDs {ids}")
        else:
            print("NO MOTORS FOUND at any baud rate")
    except Exception as e:
        print(f"ERROR: {e}")

print("\n=== SCAN COMPLETE ===")
