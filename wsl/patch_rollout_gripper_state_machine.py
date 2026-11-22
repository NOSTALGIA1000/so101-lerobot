from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

old = '''    # Optional gripper timing gate. Assumption for SO-ARM101 LeRobot actions:
    # larger gripper.pos is more open, smaller is more closed. It keeps the
    # gripper open before grasp-ready, then lets ACT's original close command
    # pass through after grasp-ready.
    if os.environ.get("ROLLOUT_GRIPPER_OPEN_UNTIL_GRASP_READY", "0") == "1":
        open_value = float(os.environ.get("ROLLOUT_GRIPPER_OPEN_VALUE", "35") or 35)
        if not grasp_ready:
            for key, value in list(action_dict.items()):
                if "gripper" in key.lower():
                    action_dict[key] = max(value, open_value)

    # Optional elbow bias. Prefer trigger=grasp_gate. The legacy trigger
'''

new = '''    # Optional gripper timing gate. Assumption for SO-ARM101 LeRobot actions:
    # larger gripper.pos is more open, smaller is more closed.
    #
    # Modes:
    # - grasp_ready: keep open until the joint-pose gate is ready.
    # - open_then_close_intent: keep open until ACT first expresses an open
    #   intent, then later expresses a close intent while the arm is in a
    #   grasp-like pose. This avoids using a simple gripper threshold as a
    #   phase trigger, because V2/V7 can be close-like from t=0.
    gripper_gate_mode = os.environ.get("ROLLOUT_GRIPPER_TIMING_GATE", "").strip().lower()
    if os.environ.get("ROLLOUT_GRIPPER_OPEN_UNTIL_GRASP_READY", "0") == "1" or gripper_gate_mode:
        open_value = float(os.environ.get("ROLLOUT_GRIPPER_OPEN_VALUE", "35") or 35)
        allow_close = grasp_ready
        raw_gripper_value = None
        for key, value in action_dict.items():
            if "gripper" in key.lower():
                raw_gripper_value = value
                break

        if gripper_gate_mode == "open_then_close_intent":
            open_seen_min = float(os.environ.get("ROLLOUT_GRIPPER_OPEN_SEEN_MIN", "20") or 20)
            close_intent_max = float(os.environ.get("ROLLOUT_GRIPPER_CLOSE_INTENT_MAX", "8") or 8)
            pose_ok = (
                shoulder_lift is not None
                and elbow_flex is not None
                and wrist_flex is not None
                and shoulder_lift > float(os.environ.get("ROLLOUT_CLOSE_SHOULDER_LIFT_MIN", "28") or 28)
                and elbow_flex < float(os.environ.get("ROLLOUT_CLOSE_ELBOW_FLEX_MAX", "-40") or -40)
                and wrist_flex > float(os.environ.get("ROLLOUT_CLOSE_WRIST_FLEX_MIN", "98") or 98)
            )
            open_seen = getattr(send_next_action, "_codex_gripper_open_seen", False)
            if raw_gripper_value is not None and raw_gripper_value >= open_seen_min:
                open_seen = True
            send_next_action._codex_gripper_open_seen = open_seen
            close_intent = raw_gripper_value is not None and raw_gripper_value <= close_intent_max
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

        if not allow_close:
            for key, value in list(action_dict.items()):
                if "gripper" in key.lower():
                    action_dict[key] = max(value, open_value)

    # Optional elbow bias. Prefer trigger=grasp_gate. The legacy trigger
'''

if "ROLLOUT_GRIPPER_TIMING_GATE" in text:
    print("ROLLOUT_GRIPPER_TIMING_GATE already present; no change")
elif old not in text:
    raise SystemExit("target block not found")
else:
    core.write_text(text.replace(old, new), encoding="utf-8")
    print("patched", core)
