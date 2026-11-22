from pathlib import Path
p = Path('/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py')
s = p.read_text()
bak = p.with_suffix(p.suffix + '.bak_delayed_grasp_hold')
if not bak.exists():
    bak.write_text(s)
old = '''            grasp_pose_hold_frames = int(float(os.environ.get("ROLLOUT_GRASP_POSE_HOLD_FRAMES", "0") or 0))
            if grasp_pose_hold_frames > 0:
                hold_remaining = int(getattr(send_next_action, "_codex_grasp_pose_hold_remaining", 0) or 0)
                hold_started = bool(getattr(send_next_action, "_codex_grasp_pose_hold_started", False))
                if allow_close and not hold_started:
                    send_next_action._codex_grasp_pose_hold_remaining = grasp_pose_hold_frames
                    send_next_action._codex_grasp_pose_hold_pending_capture = True
                    send_next_action._codex_grasp_pose_hold_started = True
                elif hold_remaining > 0:
                    allow_close = True
'''
new = '''            grasp_pose_hold_frames = int(float(os.environ.get("ROLLOUT_GRASP_POSE_HOLD_FRAMES", "0") or 0))
            if grasp_pose_hold_frames > 0:
                hold_remaining = int(getattr(send_next_action, "_codex_grasp_pose_hold_remaining", 0) or 0)
                delay_remaining = int(getattr(send_next_action, "_codex_grasp_pose_hold_delay_remaining", 0) or 0)
                hold_started = bool(getattr(send_next_action, "_codex_grasp_pose_hold_started", False))
                hold_delay_frames = int(float(os.environ.get("ROLLOUT_GRASP_POSE_HOLD_DELAY_FRAMES", "0") or 0))
                if allow_close and not hold_started:
                    send_next_action._codex_grasp_pose_hold_started = True
                    if hold_delay_frames > 0:
                        send_next_action._codex_grasp_pose_hold_delay_remaining = hold_delay_frames
                    else:
                        send_next_action._codex_grasp_pose_hold_remaining = grasp_pose_hold_frames
                        send_next_action._codex_grasp_pose_hold_pending_capture = True
                elif delay_remaining > 0:
                    allow_close = True
                    delay_remaining -= 1
                    send_next_action._codex_grasp_pose_hold_delay_remaining = delay_remaining
                    if delay_remaining == 0:
                        send_next_action._codex_grasp_pose_hold_remaining = grasp_pose_hold_frames
                        send_next_action._codex_grasp_pose_hold_pending_capture = True
                elif hold_remaining > 0:
                    allow_close = True
'''
if old not in s:
    raise SystemExit('delay patch target not found')
s = s.replace(old, new, 1)
p.write_text(s)
print('patched delayed hold')
