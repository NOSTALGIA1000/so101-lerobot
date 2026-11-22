from pathlib import Path
p = Path('/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py')
s = p.read_text()
bak = p.with_suffix(p.suffix + '.bak_macro_clamp_pose_hold')
if not bak.exists():
    bak.write_text(s)
old_start = '''        if bool(locals().get("allow_close", False)) and not getattr(send_next_action, "_codex_after_grasp_macro_started", False):
            send_next_action._codex_after_grasp_macro_started = True
            send_next_action._codex_after_grasp_macro_frame = 0
'''
new_start = '''        if bool(locals().get("allow_close", False)) and not getattr(send_next_action, "_codex_after_grasp_macro_started", False):
            send_next_action._codex_after_grasp_macro_started = True
            send_next_action._codex_after_grasp_macro_frame = 0
            macro_hold_keys_env = os.environ.get(
                "ROLLOUT_AFTER_GRASP_CLAMP_HOLD_KEYS",
                "shoulder_pan.pos,shoulder_lift.pos,elbow_flex.pos,wrist_flex.pos,wrist_roll.pos",
            )
            macro_hold_keys = [key.strip() for key in macro_hold_keys_env.split(",") if key.strip()]
            send_next_action._codex_after_grasp_clamp_pose = {
                key: action_dict[key] for key in macro_hold_keys if key in action_dict
            }
'''
if old_start not in s:
    raise SystemExit('macro start block not found')
s=s.replace(old_start,new_start,1)
old_clamp = '''            if frame < phase1:
                target = {
                    "gripper.pos": close_g,
                }
                phase = "clamp"
'''
new_clamp = '''            if frame < phase1:
                target = dict(getattr(send_next_action, "_codex_after_grasp_clamp_pose", {}) or {})
                target["gripper.pos"] = close_g
                phase = "clamp_pose_hold"
'''
if old_clamp not in s:
    raise SystemExit('macro clamp block not found')
s=s.replace(old_clamp,new_clamp,1)
p.write_text(s)
print('patched macro clamp pose hold')
