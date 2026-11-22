#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# V2 100K + visual servo place — DRY RUN
# ============================================================================
# Detect white target + purple cube from scene camera via ZMQ.
# Log dx/dy per frame, save debug images, but do NOT control robot.
#
# When ready for live test: change ROLLOUT_SCENE_SERVO_DRY_RUN to "0".
# ============================================================================

# ---- gripper / Z-bias (same proven grasp settings) ------------------------
unset ROLLOUT_GRASP_GATE || true
unset ROLLOUT_ELBOW_BIAS || true
unset ROLLOUT_ELBOW_BIAS_TRIGGER || true
unset ROLLOUT_SHOULDER_LIFT_BIAS || true
unset ROLLOUT_SHOULDER_LIFT_BIAS_TRIGGER || true
unset ROLLOUT_GRIPPER_CLOSE_LATCH || true
unset ROLLOUT_GRASP_POSE_HOLD_FRAMES || true
unset ROLLOUT_GRASP_POSE_HOLD_DELAY_FRAMES || true
unset ROLLOUT_GRIPPER_CLOSE_HOLD_FRAMES || true

export ROLLOUT_GRIPPER_TIMING_GATE="open_then_close_intent"
export ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN="0"
export ROLLOUT_GRIPPER_OPEN_VALUE="45"
export ROLLOUT_GRIPPER_CLOSE_INTENT_MAX="10"
export ROLLOUT_GRIPPER_CLOSE_DELAY_HITS="3"

export ROLLOUT_CLOSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_CLOSE_ELBOW_FLEX_MAX="-54"
export ROLLOUT_CLOSE_WRIST_FLEX_MIN="101"

export ROLLOUT_Z_BIAS="6.0"
export ROLLOUT_Z_BIAS_TRIGGER="pose"
export ROLLOUT_Z_POSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_Z_POSE_ELBOW_FLEX_MAX="-47"
export ROLLOUT_Z_POSE_WRIST_FLEX_MIN="100"
export ROLLOUT_ELBOW_BIAS="-8"
export ROLLOUT_ELBOW_BIAS_TRIGGER="grasp_gate"
export ROLLOUT_WRIST_GRASP_ENABLE="0"
# ---- scene camera grasp assist (disabled — occlusion not viable) ---------
export ROLLOUT_SCENE_GRASP_ENABLE="0"

# ---- after-grasp: visual servo place (DRY RUN) ----------------------------
export ROLLOUT_AFTER_GRASP_MACRO="visual_servo_place"
export ROLLOUT_AFTER_GRASP_CLOSE_VALUE="3"
export ROLLOUT_AFTER_GRASP_OPEN_VALUE="45"
export ROLLOUT_AFTER_GRASP_HOLD_FRAMES="5"
export ROLLOUT_AFTER_GRASP_DEEPEN_FRAMES="15"
export ROLLOUT_DEEPEN_ELBOW_TOTAL="-8"
export ROLLOUT_DEEPEN_SHOULDER_LIFT_TOTAL="-5"
export ROLLOUT_AFTER_GRASP_LIFT_FRAMES="10"
export ROLLOUT_AFTER_GRASP_CLAMP_HOLD_KEYS="shoulder_pan.pos,shoulder_lift.pos,elbow_flex.pos,wrist_flex.pos,wrist_roll.pos"

export ROLLOUT_MACRO_LIFT_SHOULDER_LIFT="28"
export ROLLOUT_MACRO_LIFT_ELBOW_FLEX="-40"
export ROLLOUT_MACRO_LIFT_WRIST_FLEX="101"
export ROLLOUT_MACRO_PLACE_SHOULDER_LIFT="25"
export ROLLOUT_MACRO_PLACE_ELBOW_FLEX="-55"
export ROLLOUT_MACRO_PLACE_WRIST_FLEX="100"
# ROLLOUT_SCENE_SERVO_PLACE_CUBE_AREA_MAX=0  # disabled until threshold known

# ---- visual servo parameters ----------------------------------------------
export ROLLOUT_SCENE_SERVO_DRY_RUN="1"          # 1 = detect+log only, 0 = live control
export ROLLOUT_SCENE_SERVO_DX_THRESHOLD="20"
export ROLLOUT_SCENE_SERVO_DY_THRESHOLD="20"
export ROLLOUT_SCENE_SERVO_STABLE_FRAMES="10"
export ROLLOUT_SCENE_SERVO_K_PAN="0.003"
export ROLLOUT_SCENE_SERVO_K_ELBOW="0.003"
export ROLLOUT_SCENE_SERVO_MAX_STEPS="300"
export ROLLOUT_SCENE_SERVO_LOG_DIR="$HOME/lerobot_outputs/rollouts/scene_servo_debug"
export ROLLOUT_SCENE_SERVO_SAVE_EVERY="5"

# ---- joint delta limiting (safety) -------------------------------------------
export ROLLOUT_MAX_DELTA_SHOULDER_PAN="1.0"
export ROLLOUT_MAX_DELTA_SHOULDER_LIFT="1.0"
export ROLLOUT_MAX_DELTA_ELBOW_FLEX="1.0"
export ROLLOUT_MAX_DELTA_WRIST_FLEX="1.5"
export ROLLOUT_MAX_DELTA_WRIST_ROLL="1.5"
export ROLLOUT_MAX_DELTA_GRIPPER="10.0"

# ---- rollout config --------------------------------------------------------
export ROLLOUT_TASK="Pick up the visible purple cube, lift it, then use scene camera visual servo to place it on the white target. DRY RUN — detect only, no robot control."
export ROLLOUT_DURATION="15"

export ROLLOUT_DEBUG_AFTER_GRASP_MACRO="1"
export ROLLOUT_DEBUG_ACTION="0"
export ROLLOUT_LOG_SUFFIX="_v2_100k_scene_servo_dryrun"
export ROLLOUT_ACTION_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_scene_servo_dryrun.csv"

rm -f "$ROLLOUT_ACTION_LOG_PATH"
/usr/bin/bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
