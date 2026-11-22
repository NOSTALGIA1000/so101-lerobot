#!/usr/bin/env bash
set -euo pipefail

export ROLLOUT_ELBOW_BIAS="-3"
export ROLLOUT_ELBOW_BIAS_TRIGGER="joint_pose"

bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
