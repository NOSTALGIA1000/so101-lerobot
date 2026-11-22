#!/usr/bin/env bash
set -euo pipefail

# Empty-gripper place pose scan for SO-ARM101 + ACT V2 100K.
# Purpose:
#   Force the after-grasp macro at rollout start and scan several shoulder_pan
#   values while holding a fixed place pose. Use scene camera / visual feedback
#   to identify which pan aligns gripper with the white target zone.
#
# Safety:
#   This script does not grasp. Keep cube and obstacles clear from gripper path.

export ROLLOUT_FORCE_MACRO_AT_START=1
export ROLLOUT_AFTER_GRASP_MACRO=fixed_place
export ROLLOUT_MACRO_SCAN_PLACE_PANS="${ROLLOUT_MACRO_SCAN_PLACE_PANS:-8,12,16,20}"
export ROLLOUT_MACRO_SCAN_HOLD_FRAMES="${ROLLOUT_MACRO_SCAN_HOLD_FRAMES:-60}"

# Fixed place-pose joints. Pan is replaced by each scan value above.
export ROLLOUT_MACRO_PLACE_SHOULDER_LIFT="${ROLLOUT_MACRO_PLACE_SHOULDER_LIFT:-45}"
export ROLLOUT_MACRO_PLACE_ELBOW_FLEX="${ROLLOUT_MACRO_PLACE_ELBOW_FLEX:--52}"
export ROLLOUT_MACRO_PLACE_WRIST_FLEX="${ROLLOUT_MACRO_PLACE_WRIST_FLEX:-100}"
export ROLLOUT_AFTER_GRASP_OPEN_VALUE="${ROLLOUT_AFTER_GRASP_OPEN_VALUE:-45}"

export ROLLOUT_DURATION="${ROLLOUT_DURATION:-12}"
export ROLLOUT_TASK="Empty gripper place pose scan. Do not pick. Hold safe pose over target."
export ROLLOUT_LOG_SUFFIX="_place_pose_scene_scan"
export ROLLOUT_DEBUG_AFTER_GRASP_MACRO=1

bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
