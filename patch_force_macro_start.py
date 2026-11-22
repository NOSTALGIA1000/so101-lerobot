from pathlib import Path
p=Path('/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py')
s=p.read_text()
bak=p.with_suffix(p.suffix+'.bak_force_macro_start')
if not bak.exists(): bak.write_text(s)
old='''        if bool(locals().get("allow_close", False)) and not getattr(send_next_action, "_codex_after_grasp_macro_started", False):
            send_next_action._codex_after_grasp_macro_started = True
            send_next_action._codex_after_grasp_macro_frame = 0
'''
new='''        force_macro_start = os.environ.get("ROLLOUT_FORCE_MACRO_AT_START", "0") == "1"
        should_start_macro = bool(locals().get("allow_close", False)) or force_macro_start
        if should_start_macro and not getattr(send_next_action, "_codex_after_grasp_macro_started", False):
            send_next_action._codex_after_grasp_macro_started = True
            send_next_action._codex_after_grasp_macro_frame = 0
'''
if old not in s: raise SystemExit('macro start target not found')
s=s.replace(old,new,1)
p.write_text(s)
print('patched force macro start')
