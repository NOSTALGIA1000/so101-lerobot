#!/usr/bin/env bash
set -euo pipefail

# No pose bias. No checkpoint change. This run only logs visual cube-center error.
unset ROLLOUT_GRASP_GATE || true
unset ROLLOUT_ELBOW_BIAS || true
unset ROLLOUT_ELBOW_BIAS_TRIGGER || true
unset ROLLOUT_SHOULDER_PAN_BIAS || true
unset ROLLOUT_SHOULDER_PAN_BIAS_TRIGGER || true

# Keep the current best gripper timing gate.
export ROLLOUT_GRIPPER_TIMING_GATE="open_then_close_intent"
export ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN="0"
export ROLLOUT_GRIPPER_OPEN_VALUE="35"
export ROLLOUT_GRIPPER_CLOSE_INTENT_MAX="10"
export ROLLOUT_GRIPPER_CLOSE_DELAY_HITS="3"
export ROLLOUT_CLOSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_CLOSE_ELBOW_FLEX_MAX="-49"
export ROLLOUT_CLOSE_WRIST_FLEX_MIN="101"

export ROLLOUT_DEBUG_BIAS="0"
export ROLLOUT_DEBUG_GRIPPER_GATE="0"
export ROLLOUT_LOG_SUFFIX="_cube_center_log"
export ROLLOUT_ACTION_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_cube_10s_cube_center_action.csv"

# Visual logging only. Use camera=all first to validate which camera gives a stable center.
export ROLLOUT_CUBE_CENTER_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_cube_10s_cube_center.csv"
export ROLLOUT_CUBE_CENTER_CAMERA="all"
export ROLLOUT_CUBE_DETECT_MODE="${ROLLOUT_CUBE_DETECT_MODE:-auto}"
export ROLLOUT_CUBE_LOG_ONLY_CLOSE_GATE="1"

rm -f "$ROLLOUT_ACTION_LOG_PATH" "$ROLLOUT_CUBE_CENTER_LOG_PATH"
bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
