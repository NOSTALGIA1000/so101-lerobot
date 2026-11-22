from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

old = '''        ):
            action_dict["elbow_flex.pos"] = elbow_flex + elbow_bias

    # Optional Codex action trajectory logging.
'''

new = '''        ):
            action_dict["elbow_flex.pos"] = elbow_flex + elbow_bias
            if os.environ.get("ROLLOUT_DEBUG_BIAS", "0") == "1":
                import time

                print("[GRASP BIAS APPLY]", flush=True)
                print(f"time={time.time():.6f}", flush=True)
                print(f"shoulder_lift={shoulder_lift:.6f}", flush=True)
                print(f"elbow_flex_before={elbow_flex:.6f}", flush=True)
                print(f"elbow_flex_after={action_dict['elbow_flex.pos']:.6f}", flush=True)
                print(f"wrist_flex={wrist_flex:.6f}", flush=True)
                print(f"bias={elbow_bias:.6f}", flush=True)

    # Optional Codex action trajectory logging.
'''

if "ROLLOUT_DEBUG_BIAS" in text:
    print("ROLLOUT_DEBUG_BIAS already present; no change")
elif old not in text:
    raise SystemExit("target block not found")
else:
    core.write_text(text.replace(old, new), encoding="utf-8")
    print("patched", core)
