from pathlib import Path
p = Path('/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py')
s = p.read_text()
bak = p.with_suffix(p.suffix + '.bak_grasp_pose_hold')
if not bak.exists():
    bak.write_text(s)
old = '''            allow_close = close_candidate and close_hits > delay_hits_required
            if allow_close and os.environ.get("ROLLOUT_GRIPPER_CLOSE_LATCH", "0") == "1":
                send_next_action._codex_gripper_close_latched = True
'''
new = '''            allow_close = close_candidate and close_hits > delay_hits_required
            grasp_pose_hold_frames = int(float(os.environ.get("ROLLOUT_GRASP_POSE_HOLD_FRAMES", "0") or 0))
            if grasp_pose_hold_frames > 0:
                hold_remaining = int(getattr(send_next_action, "_codex_grasp_pose_hold_remaining", 0) or 0)
                hold_started = bool(getattr(send_next_action, "_codex_grasp_pose_hold_started", False))
                if allow_close and not hold_started:
                    send_next_action._codex_grasp_pose_hold_remaining = grasp_pose_hold_frames
                    send_next_action._codex_grasp_pose_hold_pending_capture = True
                    send_next_action._codex_grasp_pose_hold_started = True
                elif hold_remaining > 0:
                    allow_close = True
            if allow_close and os.environ.get("ROLLOUT_GRIPPER_CLOSE_LATCH", "0") == "1":
                send_next_action._codex_gripper_close_latched = True
'''
if old in s and 'ROLLOUT_GRASP_POSE_HOLD_FRAMES' not in s:
    s = s.replace(old, new, 1)
elif 'ROLLOUT_GRASP_POSE_HOLD_FRAMES' in s:
    print('first insertion already present')
else:
    raise SystemExit('first insertion point not found')
anchor = '''    # Optional shoulder_lift vertical-depth correction.\n'''
block = '''    # Optional finite grasp-pose hold. This is different from close latch:\n    # it freezes only the vertical grasp-pose joints for N frames after the\n    # first close permission, while leaving the gripper action free to close.\n    grasp_pose_hold_frames = int(float(os.environ.get("ROLLOUT_GRASP_POSE_HOLD_FRAMES", "0") or 0))\n    hold_remaining = int(getattr(send_next_action, "_codex_grasp_pose_hold_remaining", 0) or 0)\n    if grasp_pose_hold_frames > 0 and hold_remaining > 0:\n        hold_keys_env = os.environ.get(\n            "ROLLOUT_GRASP_POSE_HOLD_KEYS",\n            "shoulder_lift.pos,elbow_flex.pos,wrist_flex.pos",\n        )\n        hold_keys = [key.strip() for key in hold_keys_env.split(",") if key.strip()]\n        hold_pose = getattr(send_next_action, "_codex_grasp_pose_hold_pose", None)\n        if hold_pose is None or getattr(send_next_action, "_codex_grasp_pose_hold_pending_capture", False):\n            hold_pose = {key: action_dict[key] for key in hold_keys if key in action_dict}\n            send_next_action._codex_grasp_pose_hold_pose = hold_pose\n            send_next_action._codex_grasp_pose_hold_pending_capture = False\n        before_hold = {key: action_dict.get(key) for key in hold_pose}\n        for key, value in hold_pose.items():\n            action_dict[key] = value\n        send_next_action._codex_grasp_pose_hold_remaining = hold_remaining - 1\n        if os.environ.get("ROLLOUT_DEBUG_GRASP_POSE_HOLD", "0") == "1" or os.environ.get("ROLLOUT_DEBUG_BIAS", "0") == "1":\n            import time\n\n            print("[GRASP POSE HOLD]", flush=True)\n            print(f"time={time.time():.6f}", flush=True)\n            print(f"remaining_before={hold_remaining}", flush=True)\n            print(f"remaining_after={hold_remaining - 1}", flush=True)\n            print(f"hold_pose={hold_pose}", flush=True)\n            print(f"before_hold={before_hold}", flush=True)\n\n'''
if block.strip() not in s:
    if anchor not in s:
        raise SystemExit('hold insertion anchor not found')
    s = s.replace(anchor, block + anchor, 1)
else:
    print('hold block already present')
p.write_text(s)
print('patched', p)
