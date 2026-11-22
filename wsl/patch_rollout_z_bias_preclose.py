from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

marker = '''    # Optional shoulder_lift vertical-depth correction.
'''

insert = '''    # Optional Z-depth pre-close correction.
    # Default off. This only changes shoulder_lift during the close-candidate
    # window before allow_close. It does not change XY, wrist, gripper, dataset,
    # checkpoint, or the ACT approach trajectory.
    #
    # Enable with:
    #   ROLLOUT_Z_BIAS=+1 or -1
    #   ROLLOUT_Z_BIAS_PRE_CLOSE_HITS=3
    z_bias = float(os.environ.get("ROLLOUT_Z_BIAS", "0") or 0)
    z_pre_close_hits = int(float(os.environ.get("ROLLOUT_Z_BIAS_PRE_CLOSE_HITS", "3") or 3))
    if z_bias:
        close_hits_for_z = int(locals().get("close_hits", 0) or 0)
        delay_hits_for_z = int(locals().get("delay_hits_required", 0) or 0)
        # Apply only after the close gate candidate has started, but before
        # allow_close releases the gripper. This gives a small final dip into
        # the cube while the gripper is still open.
        z_window_active = (
            bool(locals().get("close_candidate", False))
            and not bool(locals().get("allow_close", False))
            and close_hits_for_z > max(0, delay_hits_for_z - z_pre_close_hits)
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

if "ROLLOUT_Z_BIAS" in text:
    print("ROLLOUT_Z_BIAS already present; no change")
elif marker not in text:
    raise SystemExit("marker not found")
else:
    core.write_text(text.replace(marker, insert + marker), encoding="utf-8")
    print("patched", core)
