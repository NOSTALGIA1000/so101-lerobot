#!/usr/bin/env bash
set -euo pipefail

# Minimal baseline variant:
# - Keep the best grasp settings unchanged.
# - Do NOT use OpenCV / retraining / checkpoint edits.
# - Change only the place macro radial component:
#   place elbow_flex from -52 to -38 so the gripper actually translates
#   instead of only rotating around shoulder_pan.

unset ROLLOUT_GRASP_GATE || true
unset ROLLOUT_ELBOW_BIAS || true
unset ROLLOUT_ELBOW_BIAS_TRIGGER || true
unset ROLLOUT_SHOULDER_LIFT_BIAS || true
unset ROLLOUT_SHOULDER_LIFT_BIAS_TRIGGER || true
unset ROLLOUT_GRIPPER_CLOSE_LATCH || true
unset ROLLOUT_GRASP_POSE_HOLD_FRAMES || true
unset ROLLOUT_GRASP_POSE_HOLD_DELAY_FRAMES || true
unset ROLLOUT_GRIPPER_CLOSE_HOLD_FRAMES || true

export ROLLOUT_GRIPPER_TIMING_GATE="open_then_close_intent"
export ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN="0"
export ROLLOUT_GRIPPER_OPEN_VALUE="45"
export ROLLOUT_GRIPPER_CLOSE_INTENT_MAX="10"
export ROLLOUT_GRIPPER_CLOSE_DELAY_HITS="3"

export ROLLOUT_CLOSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_CLOSE_ELBOW_FLEX_MAX="-49"
export ROLLOUT_CLOSE_WRIST_FLEX_MIN="101"

export ROLLOUT_Z_BIAS="6.0"
export ROLLOUT_Z_BIAS_TRIGGER="pose"
export ROLLOUT_Z_POSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_Z_POSE_ELBOW_FLEX_MAX="-47"
export ROLLOUT_Z_POSE_WRIST_FLEX_MIN="100"

export ROLLOUT_AFTER_GRASP_MACRO="fixed_place"
export ROLLOUT_AFTER_GRASP_CLOSE_VALUE="3"
export ROLLOUT_AFTER_GRASP_OPEN_VALUE="45"
export ROLLOUT_AFTER_GRASP_HOLD_FRAMES="45"
export ROLLOUT_AFTER_GRASP_LIFT_FRAMES="60"
export ROLLOUT_AFTER_GRASP_MOVE_FRAMES="90"
export ROLLOUT_AFTER_GRASP_LOWER_FRAMES="45"
export ROLLOUT_AFTER_GRASP_RELEASE_FRAMES="45"
export ROLLOUT_AFTER_GRASP_CLAMP_HOLD_KEYS="shoulder_pan.pos,shoulder_lift.pos,elbow_flex.pos,wrist_flex.pos,wrist_roll.pos"

export ROLLOUT_MACRO_LIFT_SHOULDER_LIFT="28"
export ROLLOUT_MACRO_LIFT_ELBOW_FLEX="-40"
export ROLLOUT_MACRO_LIFT_WRIST_FLEX="101"

# Place target: slight left yaw + radial extension.
export ROLLOUT_MACRO_PLACE_SHOULDER_PAN="5.0"
export ROLLOUT_MACRO_PLACE_SHOULDER_LIFT="42"
export ROLLOUT_MACRO_PLACE_ELBOW_FLEX="-38"
export ROLLOUT_MACRO_PLACE_WRIST_FLEX="100"

export ROLLOUT_TASK="Pick up the visible cube, lift it, translate it to the white target zone, and release it there."
export ROLLOUT_DURATION="22"

export ROLLOUT_DEBUG_Z_BIAS="0"
export ROLLOUT_DEBUG_AFTER_GRASP_MACRO="1"
export ROLLOUT_DEBUG_BIAS="0"
export ROLLOUT_DEBUG_GRIPPER_GATE="0"
export ROLLOUT_LOG_SUFFIX="_z_p6_macro_place_elbow_extend"
export ROLLOUT_ACTION_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_cube_22s_z_p6_macro_place_elbow_extend.csv"

rm -f "$ROLLOUT_ACTION_LOG_PATH"
bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
