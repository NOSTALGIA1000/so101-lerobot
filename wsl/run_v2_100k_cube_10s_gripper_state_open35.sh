#!/usr/bin/env bash
set -euo pipefail

unset ROLLOUT_GRASP_GATE || true
unset ROLLOUT_ELBOW_BIAS || true
unset ROLLOUT_ELBOW_BIAS_TRIGGER || true

export ROLLOUT_GRIPPER_TIMING_GATE="open_then_close_intent"
export ROLLOUT_GRIPPER_OPEN_VALUE="35"
export ROLLOUT_GRIPPER_OPEN_SEEN_MIN="20"
export ROLLOUT_GRIPPER_CLOSE_INTENT_MAX="8"
export ROLLOUT_CLOSE_SHOULDER_LIFT_MIN="28"
export ROLLOUT_CLOSE_ELBOW_FLEX_MAX="-40"
export ROLLOUT_CLOSE_WRIST_FLEX_MIN="98"

export ROLLOUT_DEBUG_BIAS="1"
export ROLLOUT_LOG_SUFFIX="_gripper_state_open35"
export ROLLOUT_ACTION_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_cube_10s_gripper_state_open35.csv"

rm -f "$ROLLOUT_ACTION_LOG_PATH"
bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
