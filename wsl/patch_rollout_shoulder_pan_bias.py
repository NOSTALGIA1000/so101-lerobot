from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

marker = '''    # Optional elbow bias. Prefer trigger=grasp_gate. The legacy trigger
'''

insert = '''    # Optional shoulder_pan center correction.
    # Default off. This is for lateral cube-center calibration only.
    # Use tiny values first, e.g. +/-0.5 degree, and only during the close gate
    # candidate/allowed phase so the approach trajectory remains ACT-native.
    shoulder_pan_bias = float(os.environ.get("ROLLOUT_SHOULDER_PAN_BIAS", "0") or 0)
    shoulder_pan_trigger = os.environ.get("ROLLOUT_SHOULDER_PAN_BIAS_TRIGGER", "").strip().lower()
    if shoulder_pan_bias and shoulder_pan_trigger == "close_gate":
        close_gate_active = bool(locals().get("close_candidate", False) or locals().get("allow_close", False))
        if close_gate_active and "shoulder_pan.pos" in action_dict:
            shoulder_pan_before = action_dict["shoulder_pan.pos"]
            action_dict["shoulder_pan.pos"] = shoulder_pan_before + shoulder_pan_bias
            if os.environ.get("ROLLOUT_DEBUG_GRIPPER_GATE", "0") == "1" or os.environ.get("ROLLOUT_DEBUG_BIAS", "0") == "1":
                import time

                print("[SHOULDER PAN BIAS APPLY]", flush=True)
                print(f"time={time.time():.6f}", flush=True)
                print(f"shoulder_pan_before={shoulder_pan_before:.6f}", flush=True)
                print(f"shoulder_pan_after={action_dict['shoulder_pan.pos']:.6f}", flush=True)
                print(f"bias={shoulder_pan_bias:.6f}", flush=True)
                print(f"close_gate_active={close_gate_active}", flush=True)

'''

if "ROLLOUT_SHOULDER_PAN_BIAS" in text:
    print("ROLLOUT_SHOULDER_PAN_BIAS already present; no change")
elif marker not in text:
    raise SystemExit("marker not found")
else:
    core.write_text(text.replace(marker, insert + marker), encoding="utf-8")
    print("patched", core)
