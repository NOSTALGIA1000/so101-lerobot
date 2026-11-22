from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

old = '''            allow_close = close_candidate and close_hits > delay_hits_required
            if os.environ.get("ROLLOUT_DEBUG_BIAS", "0") == "1":
'''

new = '''            allow_close = close_candidate and close_hits > delay_hits_required
            if allow_close and os.environ.get("ROLLOUT_GRIPPER_CLOSE_LATCH", "0") == "1":
                send_next_action._codex_gripper_close_latched = True
            if os.environ.get("ROLLOUT_GRIPPER_CLOSE_LATCH", "0") == "1" and getattr(
                send_next_action, "_codex_gripper_close_latched", False
            ):
                allow_close = True
            if os.environ.get("ROLLOUT_DEBUG_BIAS", "0") == "1":
'''

old_debug = '''                print(f"allow_close={allow_close}", flush=True)
'''

new_debug = '''                print(f"allow_close={allow_close}", flush=True)
                print(f"close_latched={getattr(send_next_action, '_codex_gripper_close_latched', False)}", flush=True)
'''

if "ROLLOUT_GRIPPER_CLOSE_LATCH" in text:
    print("ROLLOUT_GRIPPER_CLOSE_LATCH already present; no change")
else:
    if old not in text:
        raise SystemExit("allow_close block not found")
    text = text.replace(old, new)
    if old_debug in text:
        text = text.replace(old_debug, new_debug)
    core.write_text(text, encoding="utf-8")
    print("patched", core)
