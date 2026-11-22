#!/usr/bin/env bash
set -euo pipefail

export ROLLOUT_ELBOW_BIAS="-3"
export ROLLOUT_ELBOW_BIAS_TRIGGER="joint_pose"
export ROLLOUT_DEBUG_BIAS="1"
export ROLLOUT_LOG_SUFFIX="_elbow_m3_debug"

bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
