#!/usr/bin/env bash
set -euo pipefail

unset ROLLOUT_GRASP_GATE || true
unset ROLLOUT_ELBOW_BIAS || true
unset ROLLOUT_ELBOW_BIAS_TRIGGER || true
unset ROLLOUT_SHOULDER_PAN_BIAS || true
unset ROLLOUT_SHOULDER_PAN_BIAS_TRIGGER || true
unset ROLLOUT_SHOULDER_LIFT_BIAS || true
unset ROLLOUT_SHOULDER_LIFT_BIAS_TRIGGER || true
unset ROLLOUT_GRIPPER_CLOSE_LATCH || true
unset ROLLOUT_GRASP_POSE_HOLD_FRAMES || true
unset ROLLOUT_GRASP_POSE_HOLD_DELAY_FRAMES || true
unset ROLLOUT_GRIPPER_CLOSE_HOLD_FRAMES || true
unset ROLLOUT_AFTER_GRASP_MACRO || true

export ROLLOUT_GRIPPER_TIMING_GATE="open_then_close_intent"
export ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN="0"
export ROLLOUT_GRIPPER_OPEN_VALUE="45"
export ROLLOUT_GRIPPER_CLOSE_INTENT_MAX="10"
export ROLLOUT_GRIPPER_CLOSE_DELAY_HITS="3"

export ROLLOUT_CLOSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_CLOSE_ELBOW_FLEX_MAX="-49"
export ROLLOUT_CLOSE_WRIST_FLEX_MIN="101"

# Keep the current successful grasp-depth direction while logging the vision error.
export ROLLOUT_Z_BIAS="5.0"
export ROLLOUT_Z_BIAS_TRIGGER="pose"
export ROLLOUT_Z_POSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_Z_POSE_ELBOW_FLEX_MAX="-47"
export ROLLOUT_Z_POSE_WRIST_FLEX_MIN="100"

export ROLLOUT_CUBE_CENTER_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_cube_10s_cube_center_scene_auto_cc.csv"
export ROLLOUT_CUBE_CENTER_CAMERA="scene"
export ROLLOUT_CUBE_DETECT_MODE="${ROLLOUT_CUBE_DETECT_MODE:-auto}"
export ROLLOUT_CUBE_MIN_AREA="${ROLLOUT_CUBE_MIN_AREA:-12}"
export ROLLOUT_CUBE_LOG_ONLY_CLOSE_GATE="0"

export ROLLOUT_DEBUG_Z_BIAS="0"
export ROLLOUT_DEBUG_BIAS="0"
export ROLLOUT_DEBUG_GRIPPER_GATE="0"
export ROLLOUT_LOG_SUFFIX="_cube_center_scene_auto_cc"
export ROLLOUT_ACTION_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_cube_10s_cube_center_scene_auto_cc_action.csv"

rm -f "$ROLLOUT_ACTION_LOG_PATH" "$ROLLOUT_CUBE_CENTER_LOG_PATH"
bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
