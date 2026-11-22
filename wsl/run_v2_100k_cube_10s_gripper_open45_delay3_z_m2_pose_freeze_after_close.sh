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

export ROLLOUT_GRIPPER_TIMING_GATE="open_then_close_intent"
export ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN="0"
export ROLLOUT_GRIPPER_OPEN_VALUE="45"
export ROLLOUT_GRIPPER_CLOSE_INTENT_MAX="10"
export ROLLOUT_GRIPPER_CLOSE_DELAY_HITS="3"
export ROLLOUT_GRIPPER_CLOSE_HOLD_FRAMES="240"

export ROLLOUT_CLOSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_CLOSE_ELBOW_FLEX_MAX="-49"
export ROLLOUT_CLOSE_WRIST_FLEX_MIN="101"

export ROLLOUT_Z_BIAS="-2.0"
export ROLLOUT_Z_BIAS_TRIGGER="pose"
export ROLLOUT_Z_POSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_Z_POSE_ELBOW_FLEX_MAX="-47"
export ROLLOUT_Z_POSE_WRIST_FLEX_MIN="100"

# Diagnostic: after close is allowed, keep the whole arm pose frozen for the
# rest of this 10s rollout. This separates "can the gripper clamp the cube at
# waist depth?" from "does ACT lift too early?".
export ROLLOUT_GRASP_POSE_HOLD_DELAY_FRAMES="4"
export ROLLOUT_GRASP_POSE_HOLD_FRAMES="240"
export ROLLOUT_GRASP_POSE_HOLD_KEYS="shoulder_pan.pos,shoulder_lift.pos,elbow_flex.pos,wrist_flex.pos,wrist_roll.pos"

export ROLLOUT_DEBUG_Z_BIAS="1"
export ROLLOUT_DEBUG_GRASP_POSE_HOLD="1"
export ROLLOUT_DEBUG_BIAS="0"
export ROLLOUT_DEBUG_GRIPPER_GATE="0"
export ROLLOUT_LOG_SUFFIX="_open45_delay3_z_m2_pose_freeze_after_close"
export ROLLOUT_ACTION_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_cube_10s_open45_delay3_z_m2_pose_freeze_after_close.csv"

rm -f "$ROLLOUT_ACTION_LOG_PATH"
bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
