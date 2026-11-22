from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

old = '''            close_candidate = bool(open_seen and close_intent and pose_ok)
            delay_hits_required = int(float(os.environ.get("ROLLOUT_GRIPPER_CLOSE_DELAY_HITS", "0") or 0))
'''

new = '''            require_open_seen = os.environ.get("ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN", "1") == "1"
            open_condition = open_seen if require_open_seen else True
            close_candidate = bool(open_condition and close_intent and pose_ok)
            delay_hits_required = int(float(os.environ.get("ROLLOUT_GRIPPER_CLOSE_DELAY_HITS", "0") or 0))
'''

old_debug = '''                print(f"open_seen={open_seen}", flush=True)
                print(f"close_intent={close_intent}", flush=True)
'''

new_debug = '''                print(f"open_seen={open_seen}", flush=True)
                print(f"require_open_seen={require_open_seen}", flush=True)
                print(f"close_intent={close_intent}", flush=True)
'''

if "ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN" in text:
    print("ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN already present; no change")
else:
    if old not in text:
        raise SystemExit("target close_candidate block not found")
    text = text.replace(old, new)
    if old_debug not in text:
        raise SystemExit("target debug block not found")
    text = text.replace(old_debug, new_debug)
    core.write_text(text, encoding="utf-8")
    print("patched", core)
