"""
Windows view copy for SO-ARM101 rollout action postprocess.

This is a readable copy of the key function from:
  /home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py

Runtime source has already been patched in WSL. This file is only for inspection
from Windows/VS Code.
"""


def send_next_action(
    obs_processed: dict,
    obs_raw: dict,
    ctx,
    interpolator,
) -> dict | None:
    """Dispatch the next action to the robot."""
    engine = ctx.policy.inference
    features = ctx.data.dataset_features
    ordered_keys = ctx.data.ordered_action_keys

    if interpolator.needs_new_action():
        obs_frame = build_dataset_frame(features, obs_processed, prefix=OBS_STR)
        action_tensor = engine.get_action(obs_frame)
        if action_tensor is not None:
            interpolator.add(action_tensor.cpu())

    interp = interpolator.get()
    if interp is None:
        return None

    if len(interp) != len(ordered_keys):
        raise ValueError(f"Interpolated tensor length ({len(interp)}) != action keys ({len(ordered_keys)})")

    action_dict = {k: interp[i].item() for i, k in enumerate(ordered_keys)}

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


# Current tested settings:
#   aggressive: threshold=50, bias=15  -> closed too early
#   conservative: threshold=35, bias=10
#
# For "gripper closes too early":
#   lower threshold first, e.g. threshold=25, bias=10
#
# For "gripper timing OK but force/closure insufficient":
#   keep threshold and increase bias, e.g. threshold=35, bias=15
#
# For "end-effector depth too shallow":
#   do NOT solve with gripper bias.
#   Need inspect ordered_keys, then add small bias to the correct arm joint
#   only during close phase.
