from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

start = text.index("    # Codex SO-ARM101 grasp-pose elbow bias.")
end = text.index("    # Optional Codex action trajectory logging.", start)

replacement = '''    # Codex SO-ARM101 stateful grasp-ready gate and optional postprocess.
    #
    # Default is off. The gate avoids using gripper threshold because V2/V7 logs
    # show gripper is close-like for most of rollout. Instead it detects a
    # stable grasp-like joint pose for several consecutive frames.
    #
    # Recommended first validation:
    #   ROLLOUT_GRASP_GATE=joint_pose_stable
    #   ROLLOUT_GRASP_READY_MIN_HITS=8
    #   ROLLOUT_ELBOW_BIAS=-1
    #   ROLLOUT_ELBOW_BIAS_TRIGGER=grasp_gate
    #   ROLLOUT_GRIPPER_OPEN_UNTIL_GRASP_READY=1
    #   ROLLOUT_GRIPPER_OPEN_VALUE=35
    grasp_gate = os.environ.get("ROLLOUT_GRASP_GATE", "").strip().lower()
    grasp_ready = False
    shoulder_lift = action_dict.get("shoulder_lift.pos")
    elbow_flex = action_dict.get("elbow_flex.pos")
    wrist_flex = action_dict.get("wrist_flex.pos")
    if grasp_gate == "joint_pose_stable":
        sl_min = float(os.environ.get("ROLLOUT_GRASP_SHOULDER_LIFT_MIN", "38") or 38)
        ef_max = float(os.environ.get("ROLLOUT_GRASP_ELBOW_FLEX_MAX", "-53") or -53)
        wf_min = float(os.environ.get("ROLLOUT_GRASP_WRIST_FLEX_MIN", "98") or 98)
        min_hits = int(float(os.environ.get("ROLLOUT_GRASP_READY_MIN_HITS", "8") or 8))
        pose_hit = (
            shoulder_lift is not None
            and elbow_flex is not None
            and wrist_flex is not None
            and shoulder_lift > sl_min
            and elbow_flex < ef_max
            and wrist_flex > wf_min
        )
        current_hits = getattr(send_next_action, "_codex_grasp_gate_hits", 0)
        current_hits = current_hits + 1 if pose_hit else 0
        send_next_action._codex_grasp_gate_hits = current_hits
        grasp_ready = current_hits >= min_hits
        if os.environ.get("ROLLOUT_DEBUG_BIAS", "0") == "1" and pose_hit:
            import time

            print("[GRASP GATE]", flush=True)
            print(f"time={time.time():.6f}", flush=True)
            print(f"pose_hit={pose_hit}", flush=True)
            print(f"hits={current_hits}", flush=True)
            print(f"ready={grasp_ready}", flush=True)
            print(f"shoulder_lift={shoulder_lift:.6f}", flush=True)
            print(f"elbow_flex={elbow_flex:.6f}", flush=True)
            print(f"wrist_flex={wrist_flex:.6f}", flush=True)

    # Optional gripper timing gate. Assumption for SO-ARM101 LeRobot actions:
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
    # joint_pose is kept for reproducibility of the overreach experiment.
    elbow_bias = float(os.environ.get("ROLLOUT_ELBOW_BIAS", "0") or 0)
    elbow_trigger = os.environ.get("ROLLOUT_ELBOW_BIAS_TRIGGER", "").strip().lower()
    apply_elbow_bias = False
    if elbow_bias and elbow_trigger == "grasp_gate":
        apply_elbow_bias = grasp_ready
    elif elbow_bias and elbow_trigger == "joint_pose":
        apply_elbow_bias = (
            shoulder_lift is not None
            and elbow_flex is not None
            and wrist_flex is not None
            and shoulder_lift > 20.0
            and elbow_flex < -30.0
            and wrist_flex > 80.0
        )
    if apply_elbow_bias and elbow_flex is not None:
        action_dict["elbow_flex.pos"] = elbow_flex + elbow_bias
        if os.environ.get("ROLLOUT_DEBUG_BIAS", "0") == "1":
            import time

            print("[GRASP BIAS APPLY]", flush=True)
            print(f"time={time.time():.6f}", flush=True)
            print(f"trigger={elbow_trigger}", flush=True)
            print(f"grasp_ready={grasp_ready}", flush=True)
            print(f"shoulder_lift={shoulder_lift:.6f}", flush=True)
            print(f"elbow_flex_before={elbow_flex:.6f}", flush=True)
            print(f"elbow_flex_after={action_dict['elbow_flex.pos']:.6f}", flush=True)
            print(f"wrist_flex={wrist_flex:.6f}", flush=True)
            print(f"bias={elbow_bias:.6f}", flush=True)

'''

if "ROLLOUT_GRASP_GATE" in text:
    print("ROLLOUT_GRASP_GATE already present; no change")
else:
    core.write_text(text[:start] + replacement + text[end:], encoding="utf-8")
    print("patched", core)
