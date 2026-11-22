from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

old = '''            close_intent = raw_gripper_value is not None and raw_gripper_value <= close_intent_max
            allow_close = bool(open_seen and close_intent and pose_ok)
            if os.environ.get("ROLLOUT_DEBUG_BIAS", "0") == "1":
                import time

                print("[GRIPPER TIMING GATE]", flush=True)
                print(f"time={time.time():.6f}", flush=True)
                print(f"raw_gripper={raw_gripper_value}", flush=True)
                print(f"open_seen={open_seen}", flush=True)
                print(f"close_intent={close_intent}", flush=True)
                print(f"pose_ok={pose_ok}", flush=True)
                print(f"allow_close={allow_close}", flush=True)
'''

new = '''            close_intent = raw_gripper_value is not None and raw_gripper_value <= close_intent_max
            close_candidate = bool(open_seen and close_intent and pose_ok)
            delay_hits_required = int(float(os.environ.get("ROLLOUT_GRIPPER_CLOSE_DELAY_HITS", "0") or 0))
            close_hits = getattr(send_next_action, "_codex_gripper_close_hits", 0)
            close_hits = close_hits + 1 if close_candidate else 0
            send_next_action._codex_gripper_close_hits = close_hits
            allow_close = close_candidate and close_hits > delay_hits_required
            if os.environ.get("ROLLOUT_DEBUG_BIAS", "0") == "1":
                import time

                print("[GRIPPER TIMING GATE]", flush=True)
                print(f"time={time.time():.6f}", flush=True)
                print(f"raw_gripper={raw_gripper_value}", flush=True)
                print(f"open_seen={open_seen}", flush=True)
                print(f"close_intent={close_intent}", flush=True)
                print(f"pose_ok={pose_ok}", flush=True)
                print(f"close_candidate={close_candidate}", flush=True)
                print(f"close_hits={close_hits}", flush=True)
                print(f"delay_hits_required={delay_hits_required}", flush=True)
                print(f"allow_close={allow_close}", flush=True)
'''

if "ROLLOUT_GRIPPER_CLOSE_DELAY_HITS" in text:
    print("ROLLOUT_GRIPPER_CLOSE_DELAY_HITS already present; no change")
elif old not in text:
    raise SystemExit("target block not found")
else:
    core.write_text(text.replace(old, new), encoding="utf-8")
    print("patched", core)
