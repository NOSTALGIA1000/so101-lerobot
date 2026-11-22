from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

old = '''        if z_trigger == "pose":
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
'''

new = '''        if z_trigger in ("pose", "pose_hold"):
            pose_z_ok = (
                shoulder_lift is not None
                and elbow_flex is not None
                and wrist_flex is not None
                and shoulder_lift > float(os.environ.get("ROLLOUT_Z_POSE_SHOULDER_LIFT_MIN", "30") or 30)
                and elbow_flex < float(os.environ.get("ROLLOUT_Z_POSE_ELBOW_FLEX_MAX", "-47") or -47)
                and wrist_flex > float(os.environ.get("ROLLOUT_Z_POSE_WRIST_FLEX_MIN", "100") or 100)
            )
            z_window_active = pose_z_ok
            if z_trigger == "pose_hold":
                z_hold_frames = int(float(os.environ.get("ROLLOUT_Z_HOLD_AFTER_CLOSE_HITS", "12") or 12))
                if bool(locals().get("allow_close", False)):
                    hold_count = getattr(send_next_action, "_codex_z_hold_after_close_count", 0) + 1
                    send_next_action._codex_z_hold_after_close_count = hold_count
                else:
                    hold_count = getattr(send_next_action, "_codex_z_hold_after_close_count", 0)
                z_window_active = pose_z_ok or (hold_count > 0 and hold_count <= z_hold_frames)
        else:
            z_window_active = (
                bool(locals().get("close_candidate", False))
                and close_hits_for_z >= 1
                and close_hits_for_z <= z_pre_close_hits
            )
'''

old_debug = '''                print(f"z_pre_close_hits={z_pre_close_hits}", flush=True)
'''

new_debug = '''                print(f"z_pre_close_hits={z_pre_close_hits}", flush=True)
                if z_trigger == "pose_hold":
                    print(f"z_hold_after_close_count={getattr(send_next_action, '_codex_z_hold_after_close_count', 0)}", flush=True)
                    print(f"z_hold_after_close_hits={os.environ.get('ROLLOUT_Z_HOLD_AFTER_CLOSE_HITS', '12')}", flush=True)
'''

if "ROLLOUT_Z_HOLD_AFTER_CLOSE_HITS" in text:
    print("ROLLOUT_Z_HOLD_AFTER_CLOSE_HITS already present; no change")
elif old not in text:
    raise SystemExit("target z trigger block not found")
else:
    text = text.replace(old, new)
    if old_debug in text:
        text = text.replace(old_debug, new_debug)
    core.write_text(text, encoding="utf-8")
    print("patched", core)
