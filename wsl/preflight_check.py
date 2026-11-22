"""Pre-flight check script for live rollout."""
import zmq
import json
import sys

# Check camera bridge
ctx = zmq.Context()
sock = ctx.socket(zmq.SUB)
sock.setsockopt_string(zmq.SUBSCRIBE, "")
sock.setsockopt(zmq.RCVTIMEO, 3000)
try:
    sock.connect("tcp://172.28.48.1:5555")
    msg = sock.recv_string()
    data = json.loads(msg)
    cameras = sorted(data.get("images", {}).keys())
    print(f"[OK] Camera bridge: {len(cameras)} cameras: {cameras}")
except Exception as e:
    print(f"[FAIL] Camera bridge: {e}")
    sys.exit(2)
finally:
    sock.close()
    ctx.term()

# Check core.py can import
sys.path.insert(0, "/home/nostalgia/lerobot_workspace/lerobot/src")
try:
    from lerobot.rollout.strategies.core import send_next_action
    print("[OK] core.py importable")
except Exception as e:
    print(f"[FAIL] core.py import: {e}")
    sys.exit(3)

print("[OK] All pre-flight checks passed.")
