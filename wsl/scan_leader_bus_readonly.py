#!/usr/bin/env python3
"""Read-only Feetech bus scanner. Pings motor IDs 1-6 on a serial port.
Does NOT write motor IDs, does NOT reconfigure. Only READ."""

import serial
import sys
import time

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM1"
BAUD_RATES = [1000000, 500000, 115200, 57600]

for br in BAUD_RATES:
    print(f"\n=== Baud rate: {br} ===")
    try:
        ser = serial.Serial(PORT, br, timeout=0.15)
        time.sleep(0.1)

        for motor_id in range(1, 7):
            # READ instruction (0x02): read 2 bytes from address 0 (Model Number)
            # Packet: 0xFF 0xFF ID 0x04 0x02 0x00 0x00 0x02 CHECKSUM
            packet = bytearray([0xFF, 0xFF, motor_id, 0x04, 0x02, 0x00, 0x00, 0x02])
            checksum = (~sum(packet[2:]) + 1) & 0xFF
            packet.append(checksum)

            ser.reset_input_buffer()
            ser.write(packet)
            ser.flush()

            resp = ser.read(10)
            if resp and len(resp) >= 6:
                # Status packet: 0xFF 0xFF ID LEN ERR PARAM_L PARAM_H CHECKSUM
                err = resp[4]
                if err != 0:
                    print(f"  ID={motor_id}: ERROR byte={err} (ID not found or comm error)")
                elif len(resp) >= 7:
                    model = resp[5] | (resp[6] << 8)
                    print(f"  ID={motor_id}: FOUND model_number={model} (STS3215=777)")
                else:
                    print(f"  ID={motor_id}: short response: {resp.hex()}")
            else:
                print(f"  ID={motor_id}: no response (timeout)")

        ser.close()

        # If we got here without serial error, stop trying other baud rates
        print(f"\nBaud {br} finished. Check results above.")
        break

    except serial.SerialException as e:
        print(f"  SERIAL ERROR: {e}")
    except Exception as e:
        print(f"  FAIL: {e}")

print("\n=== SCAN DONE ===")
