from pathlib import Path
p=Path('/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py')
s=p.read_text()
bak=p.with_suffix(p.suffix+'.bak_macro_done_hold_place')
if not bak.exists(): bak.write_text(s)
old='''            else:
                target = {"gripper.pos": open_g}
                phase = "done"
'''
new='''            else:
                target = {
                    "shoulder_pan.pos": float(os.environ.get("ROLLOUT_MACRO_PLACE_SHOULDER_PAN", "0") or 0),
                    "shoulder_lift.pos": float(os.environ.get("ROLLOUT_MACRO_PLACE_SHOULDER_LIFT", "45") or 45),
                    "elbow_flex.pos": float(os.environ.get("ROLLOUT_MACRO_PLACE_ELBOW_FLEX", "-52") or -52),
                    "wrist_flex.pos": float(os.environ.get("ROLLOUT_MACRO_PLACE_WRIST_FLEX", "100") or 100),
                    "gripper.pos": open_g,
                }
                phase = "done_hold_place"
'''
if old not in s: raise SystemExit('done block not found')
s=s.replace(old,new,1)
p.write_text(s)
print('patched macro done hold place')
