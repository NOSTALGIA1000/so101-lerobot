#!/usr/bin/env python3
import socket
import subprocess

try:
    gateway = subprocess.check_output(
        ["bash", "-lc", "ip route show default | awk '{print $3; exit}'"],
        text=True,
    ).strip()
except Exception:
    gateway = "172.28.48.1"

print(f"gateway={gateway}")
for host in [gateway, "127.0.0.1"]:
    s = socket.socket()
    s.settimeout(3)
    try:
        s.connect((host, 5555))
        print(f"tcp_5555_{host}=open")
    except Exception as exc:
        print(f"tcp_5555_{host}=closed:{exc}")
    finally:
        s.close()
