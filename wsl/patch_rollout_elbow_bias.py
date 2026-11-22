from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

marker = """    # Optional Codex action trajectory logging.
    action_log_path = os.environ.get("ROLLOUT_ACTION_LOG_PATH")
"""

insert = """    # Codex SO-ARM101 grasp-pose elbow bias.
    # Default is off. Enable with:
    #   ROLLOUT_ELBOW_BIAS=-3
    #   ROLLOUT_ELBOW_BIAS_TRIGGER=joint_pose
    #
    # This is intentionally separate from gripper postprocessing. The V2/V7
    # action logs show gripper is already in a close-like region for most of
    # rollout, so gripper thresholds are not a reliable grasp-phase trigger.
    # The joint-pose trigger activates only in the final grasp-pose region.
    elbow_bias = float(os.environ.get("ROLLOUT_ELBOW_BIAS", "0") or 0)
    elbow_trigger = os.environ.get("ROLLOUT_ELBOW_BIAS_TRIGGER", "").strip().lower()
    if elbow_bias and elbow_trigger == "joint_pose":
        shoulder_lift = action_dict.get("shoulder_lift.pos")
        elbow_flex = action_dict.get("elbow_flex.pos")
        wrist_flex = action_dict.get("wrist_flex.pos")
        if (
            shoulder_lift is not None
            and elbow_flex is not None
            and wrist_flex is not None
            and shoulder_lift > 20.0
            and elbow_flex < -30.0
            and wrist_flex > 80.0
        ):
            action_dict["elbow_flex.pos"] = elbow_flex + elbow_bias

"""

if "ROLLOUT_ELBOW_BIAS" in text:
    print("ROLLOUT_ELBOW_BIAS already present; no change")
else:
    if marker not in text:
        raise SystemExit("marker not found")
    text = text.replace(marker, insert + marker)
    core.write_text(text, encoding="utf-8")
    print("patched", core)
