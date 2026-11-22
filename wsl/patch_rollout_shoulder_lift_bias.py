from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

marker = '''    # Optional shoulder_pan center correction.
'''

insert = '''    # Optional shoulder_lift vertical-depth correction.
    # Default off. This is for Z-depth calibration only after lateral alignment
    # is correct. Apply only during the close gate phase to preserve ACT's
    # approach trajectory.
    shoulder_lift_bias = float(os.environ.get("ROLLOUT_SHOULDER_LIFT_BIAS", "0") or 0)
    shoulder_lift_trigger = os.environ.get("ROLLOUT_SHOULDER_LIFT_BIAS_TRIGGER", "").strip().lower()
    if shoulder_lift_bias and shoulder_lift_trigger == "close_gate":
        close_gate_active = bool(locals().get("close_candidate", False) or locals().get("allow_close", False))
        if close_gate_active and "shoulder_lift.pos" in action_dict:
            shoulder_lift_before = action_dict["shoulder_lift.pos"]
            action_dict["shoulder_lift.pos"] = shoulder_lift_before + shoulder_lift_bias
            if os.environ.get("ROLLOUT_DEBUG_GRIPPER_GATE", "0") == "1" or os.environ.get("ROLLOUT_DEBUG_BIAS", "0") == "1":
                import time

                print("[SHOULDER LIFT BIAS APPLY]", flush=True)
                print(f"time={time.time():.6f}", flush=True)
                print(f"shoulder_lift_before={shoulder_lift_before:.6f}", flush=True)
                print(f"shoulder_lift_after={action_dict['shoulder_lift.pos']:.6f}", flush=True)
                print(f"bias={shoulder_lift_bias:.6f}", flush=True)
                print(f"close_gate_active={close_gate_active}", flush=True)

'''

if "ROLLOUT_SHOULDER_LIFT_BIAS" in text:
    print("ROLLOUT_SHOULDER_LIFT_BIAS already present; no change")
elif marker not in text:
    raise SystemExit("marker not found")
else:
    core.write_text(text.replace(marker, insert + marker), encoding="utf-8")
    print("patched", core)
