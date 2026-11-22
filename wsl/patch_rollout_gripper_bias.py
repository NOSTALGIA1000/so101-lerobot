#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


CORE = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
BACKUP = CORE.with_suffix(".py.codex_gripper_bias_backup")

OLD = """    action_dict = {k: interp[i].item() for i, k in enumerate(ordered_keys)}
    processed = ctx.processors.robot_action_processor((action_dict, obs_raw))
    ctx.hardware.robot_wrapper.send_action(processed)
    return action_dict
"""

NEW = """    action_dict = {k: interp[i].item() for i, k in enumerate(ordered_keys)}

    # Codex SO-ARM101 real-test gripper postprocess.
    # Enabled only when ROLLOUT_GRIPPER_CLOSE_BIAS is set.
    # Rationale: current ACT checkpoints reach/align well but often do not close
    # the gripper enough near the cube. We bias only close-like commands, leaving
    # open commands unchanged.
    import os

    gripper_bias = float(os.environ.get("ROLLOUT_GRIPPER_CLOSE_BIAS", "0") or 0)
    gripper_threshold = float(os.environ.get("ROLLOUT_GRIPPER_CLOSE_THRESHOLD", "50") or 50)
    if gripper_bias:
        for key, value in list(action_dict.items()):
            if "gripper" in key.lower():
                if value < gripper_threshold:
                    action_dict[key] = max(0.0, min(100.0, value - gripper_bias))

    processed = ctx.processors.robot_action_processor((action_dict, obs_raw))
    ctx.hardware.robot_wrapper.send_action(processed)
    return action_dict
"""


def main() -> None:
    text = CORE.read_text()
    if NEW in text:
        print(f"already_patched={CORE}")
        return
    if OLD not in text:
        raise RuntimeError("target snippet not found; refusing to patch")
    if not BACKUP.exists():
        BACKUP.write_text(text)
        print(f"backup={BACKUP}")
    CORE.write_text(text.replace(OLD, NEW))
    print(f"patched={CORE}")


if __name__ == "__main__":
    main()
