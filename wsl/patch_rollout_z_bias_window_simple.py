from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

old = '''        z_window_active = (
            bool(locals().get("close_candidate", False))
            and not bool(locals().get("allow_close", False))
            and close_hits_for_z > max(0, delay_hits_for_z - z_pre_close_hits)
        )
'''

new = '''        z_window_active = (
            bool(locals().get("close_candidate", False))
            and close_hits_for_z >= 1
            and close_hits_for_z <= z_pre_close_hits
        )
'''

if old not in text:
    print("target z_window block not found; maybe already patched")
else:
    core.write_text(text.replace(old, new), encoding="utf-8")
    print("patched", core)
