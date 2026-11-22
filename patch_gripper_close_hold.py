from pathlib import Path
p = Path('/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py')
s = p.read_text()
bak = p.with_suffix(p.suffix + '.bak_gripper_close_hold')
if not bak.exists():
    bak.write_text(s)
old = '''            allow_close = close_candidate and close_hits > delay_hits_required
            grasp_pose_hold_frames = int(float(os.environ.get("ROLLOUT_GRASP_POSE_HOLD_FRAMES", "0") or 0))
'''
new = '''            allow_close = close_candidate and close_hits > delay_hits_required
            gripper_close_hold_frames = int(float(os.environ.get("ROLLOUT_GRIPPER_CLOSE_HOLD_FRAMES", "0") or 0))
            if gripper_close_hold_frames > 0:
                gripper_close_hold_remaining = int(getattr(send_next_action, "_codex_gripper_close_hold_remaining", 0) or 0)
                gripper_close_hold_started = bool(getattr(send_next_action, "_codex_gripper_close_hold_started", False))
                if allow_close and not gripper_close_hold_started:
                    send_next_action._codex_gripper_close_hold_remaining = gripper_close_hold_frames
                    send_next_action._codex_gripper_close_hold_started = True
                elif gripper_close_hold_remaining > 0:
                    allow_close = True
                    send_next_action._codex_gripper_close_hold_remaining = gripper_close_hold_remaining - 1
            grasp_pose_hold_frames = int(float(os.environ.get("ROLLOUT_GRASP_POSE_HOLD_FRAMES", "0") or 0))
'''
if old not in s:
    raise SystemExit('gripper close hold insertion target not found')
s = s.replace(old, new, 1)
old_dbg = '''                print(f"close_latched={getattr(send_next_action, '_codex_gripper_close_latched', False)}", flush=True)
'''
new_dbg = '''                print(f"close_latched={getattr(send_next_action, '_codex_gripper_close_latched', False)}", flush=True)
                print(f"gripper_close_hold_remaining={getattr(send_next_action, '_codex_gripper_close_hold_remaining', 0)}", flush=True)
'''
if old_dbg in s:
    s = s.replace(old_dbg, new_dbg, 1)
p.write_text(s)
print('patched gripper close hold')
