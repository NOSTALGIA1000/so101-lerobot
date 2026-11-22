#!/usr/bin/env bash
set -euo pipefail

export ROLLOUT_GRASP_GATE="joint_pose_stable"
export ROLLOUT_GRASP_READY_MIN_HITS="4"
export ROLLOUT_GRASP_SHOULDER_LIFT_MIN="38"
export ROLLOUT_GRASP_ELBOW_FLEX_MAX="-53"
export ROLLOUT_GRASP_WRIST_FLEX_MIN="98"

export ROLLOUT_GRIPPER_OPEN_UNTIL_GRASP_READY="1"
export ROLLOUT_GRIPPER_OPEN_VALUE="35"

export ROLLOUT_ELBOW_BIAS="-1"
export ROLLOUT_ELBOW_BIAS_TRIGGER="grasp_gate"

export ROLLOUT_DEBUG_BIAS="1"
export ROLLOUT_LOG_SUFFIX="_grasp_gate4_open35_elbow_m1"
export ROLLOUT_ACTION_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_cube_10s_grasp_gate4_open35_elbow_m1.csv"

rm -f "$ROLLOUT_ACTION_LOG_PATH"
bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
