#!/usr/bin/env bash
set -euo pipefail

export ROLLOUT_ELBOW_BIAS="0"
unset ROLLOUT_ELBOW_BIAS_TRIGGER || true
unset ROLLOUT_GRIPPER_CLOSE_BIAS || true
unset ROLLOUT_GRIPPER_CLOSE_THRESHOLD || true
unset ROLLOUT_DEBUG_BIAS || true
export ROLLOUT_LOG_SUFFIX="_actionlog_original"
export ROLLOUT_ACTION_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_cube_10s_actionlog_original.csv"

rm -f "$ROLLOUT_ACTION_LOG_PATH"
bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
