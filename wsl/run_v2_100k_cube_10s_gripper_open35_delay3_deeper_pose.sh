#!/usr/bin/env bash
set -euo pipefail

unset ROLLOUT_GRASP_GATE || true
unset ROLLOUT_ELBOW_BIAS || true
unset ROLLOUT_ELBOW_BIAS_TRIGGER || true

export ROLLOUT_GRIPPER_TIMING_GATE="open_then_close_intent"
export ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN="0"
export ROLLOUT_GRIPPER_OPEN_VALUE="35"
export ROLLOUT_GRIPPER_OPEN_SEEN_MIN="20"
export ROLLOUT_GRIPPER_CLOSE_INTENT_MAX="10"
export ROLLOUT_GRIPPER_CLOSE_DELAY_HITS="3"

# Deeper close gate: wait until the wrist/elbow pose is past the first-contact edge.
export ROLLOUT_CLOSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_CLOSE_ELBOW_FLEX_MAX="-49"
export ROLLOUT_CLOSE_WRIST_FLEX_MIN="101"

export ROLLOUT_DEBUG_BIAS="1"
export ROLLOUT_DEBUG_GRIPPER_GATE="1"
export ROLLOUT_LOG_SUFFIX="_gripper_open35_delay3_deeper_pose"
export ROLLOUT_ACTION_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_cube_10s_gripper_open35_delay3_deeper_pose.csv"

rm -f "$ROLLOUT_ACTION_LOG_PATH"
bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
