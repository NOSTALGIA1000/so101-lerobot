#!/usr/bin/env python3
"""Ping scan: open port without handshake, broadcast ping to find ANY motor.
Safe - read-only, no ID writing."""

import sys
from lerobot.motors.feetech import FeetechMotorsBus

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM1"

print(f"Opening {PORT} without handshake...")
try:
    # Empty motors = no expectations, just open the port
    bus = FeetechMotorsBus(port=PORT, motors={})
    bus._connect(handshake=False)
    print(f"Connected. Available baud rates: {bus.available_baudrates}")

    for br in bus.available_baudrates:
        bus.set_baudrate(br)
        ids = bus.broadcast_ping()
        if ids:
            print(f"  Baud {br}: FOUND motors: {ids}")
        else:
            print(f"  Baud {br}: no response")

    bus.port_handler.closePort()
    print("Port closed.")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("=== PING DONE ===")
