#!/usr/bin/env bash
set -euo pipefail

unset ROLLOUT_AFTER_GRASP_MACRO || true
unset ROLLOUT_GRIPPER_CLOSE_HOLD_FRAMES || true
unset ROLLOUT_GRASP_POSE_HOLD_FRAMES || true

export ROLLOUT_GRIPPER_TIMING_GATE="open_then_close_intent"
export ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN="0"
export ROLLOUT_GRIPPER_OPEN_VALUE="45"
export ROLLOUT_GRIPPER_CLOSE_INTENT_MAX="10"
export ROLLOUT_GRIPPER_CLOSE_DELAY_HITS="3"
export ROLLOUT_CLOSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_CLOSE_ELBOW_FLEX_MAX="-49"
export ROLLOUT_CLOSE_WRIST_FLEX_MIN="101"

export ROLLOUT_CUBE_CENTER_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_cube_3s_cube_center_debug.csv"
export ROLLOUT_CUBE_CENTER_CAMERA="scene"
export ROLLOUT_CUBE_DETECT_MODE="${ROLLOUT_CUBE_DETECT_MODE:-auto}"
export ROLLOUT_CUBE_MIN_AREA="${ROLLOUT_CUBE_MIN_AREA:-12}"
export ROLLOUT_CUBE_LOG_ONLY_CLOSE_GATE="0"
export ROLLOUT_CUBE_DEBUG_IMAGE_DIR="$HOME/lerobot_outputs/rollouts/cube_debug_images"
export ROLLOUT_CUBE_DEBUG_MAX_IMAGES="12"
export ROLLOUT_CUBE_DEBUG_STRIDE="5"

export ROLLOUT_TASK="Short camera debug run. Approach slowly but prioritize stable observation."
export ROLLOUT_DURATION="3"
export ROLLOUT_LOG_SUFFIX="_cube_center_debug_images"
export ROLLOUT_ACTION_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_cube_3s_cube_center_debug_action.csv"

rm -rf "$ROLLOUT_CUBE_DEBUG_IMAGE_DIR"
rm -f "$ROLLOUT_ACTION_LOG_PATH" "$ROLLOUT_CUBE_CENTER_LOG_PATH"
bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
