from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

old = '''    z_bias = float(os.environ.get("ROLLOUT_Z_BIAS", "0") or 0)
    z_pre_close_hits = int(float(os.environ.get("ROLLOUT_Z_BIAS_PRE_CLOSE_HITS", "3") or 3))
    if z_bias:
        close_hits_for_z = int(locals().get("close_hits", 0) or 0)
        delay_hits_for_z = int(locals().get("delay_hits_required", 0) or 0)
        # Apply only after the close gate candidate has started, but before
        # allow_close releases the gripper. This gives a small final dip into
        # the cube while the gripper is still open.
        z_window_active = (
            bool(locals().get("close_candidate", False))
            and close_hits_for_z >= 1
            and close_hits_for_z <= z_pre_close_hits
        )
        if z_window_active and "shoulder_lift.pos" in action_dict:
            shoulder_lift_before = action_dict["shoulder_lift.pos"]
            action_dict["shoulder_lift.pos"] = shoulder_lift_before + z_bias
            if os.environ.get("ROLLOUT_DEBUG_Z_BIAS", "0") == "1" or os.environ.get("ROLLOUT_DEBUG_BIAS", "0") == "1":
                import time

                print("[Z BIAS APPLY]", flush=True)
                print(f"time={time.time():.6f}", flush=True)
                print(f"shoulder_lift_before={shoulder_lift_before:.6f}", flush=True)
                print(f"shoulder_lift_after={action_dict['shoulder_lift.pos']:.6f}", flush=True)
                print(f"z_bias={z_bias:.6f}", flush=True)
                print(f"close_hits={close_hits_for_z}", flush=True)
                print(f"delay_hits_required={delay_hits_for_z}", flush=True)
                print(f"z_pre_close_hits={z_pre_close_hits}", flush=True)
'''

new = '''    z_bias = float(os.environ.get("ROLLOUT_Z_BIAS", "0") or 0)
    z_trigger = os.environ.get("ROLLOUT_Z_BIAS_TRIGGER", "pre_close").strip().lower()
    z_pre_close_hits = int(float(os.environ.get("ROLLOUT_Z_BIAS_PRE_CLOSE_HITS", "3") or 3))
    if z_bias:
        close_hits_for_z = int(locals().get("close_hits", 0) or 0)
        delay_hits_for_z = int(locals().get("delay_hits_required", 0) or 0)
        if z_trigger == "pose":
            z_window_active = (
                shoulder_lift is not None
                and elbow_flex is not None
                and wrist_flex is not None
                and shoulder_lift > float(os.environ.get("ROLLOUT_Z_POSE_SHOULDER_LIFT_MIN", "30") or 30)
                and elbow_flex < float(os.environ.get("ROLLOUT_Z_POSE_ELBOW_FLEX_MAX", "-47") or -47)
                and wrist_flex > float(os.environ.get("ROLLOUT_Z_POSE_WRIST_FLEX_MIN", "100") or 100)
            )
        else:
            z_window_active = (
                bool(locals().get("close_candidate", False))
                and close_hits_for_z >= 1
                and close_hits_for_z <= z_pre_close_hits
            )
        if z_window_active and "shoulder_lift.pos" in action_dict:
            shoulder_lift_before = action_dict["shoulder_lift.pos"]
            action_dict["shoulder_lift.pos"] = shoulder_lift_before + z_bias
            if os.environ.get("ROLLOUT_DEBUG_Z_BIAS", "0") == "1" or os.environ.get("ROLLOUT_DEBUG_BIAS", "0") == "1":
                import time

                print("[Z BIAS APPLY]", flush=True)
                print(f"time={time.time():.6f}", flush=True)
                print(f"trigger={z_trigger}", flush=True)
                print(f"shoulder_lift_before={shoulder_lift_before:.6f}", flush=True)
                print(f"shoulder_lift_after={action_dict['shoulder_lift.pos']:.6f}", flush=True)
                print(f"elbow_flex={elbow_flex}", flush=True)
                print(f"wrist_flex={wrist_flex}", flush=True)
                print(f"z_bias={z_bias:.6f}", flush=True)
                print(f"close_hits={close_hits_for_z}", flush=True)
                print(f"delay_hits_required={delay_hits_for_z}", flush=True)
                print(f"z_pre_close_hits={z_pre_close_hits}", flush=True)
'''

if "ROLLOUT_Z_BIAS_TRIGGER" in text:
    print("ROLLOUT_Z_BIAS_TRIGGER already present; no change")
elif old not in text:
    raise SystemExit("target z bias block not found")
else:
    core.write_text(text.replace(old, new), encoding="utf-8")
    print("patched", core)
