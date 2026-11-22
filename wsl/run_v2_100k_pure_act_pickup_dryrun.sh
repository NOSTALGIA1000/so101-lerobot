#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# V2 100K — Pure ACT pickup test (no after-grasp macro)
# ============================================================================
# ACT policy → approach → grasp → lift (no visual servo, no fixed_place).
# State machine logging enabled (STATE_PICK → STATE_GRASP).
# Joint delta limiting enabled for safety.
#
# Purpose: Verify ACT can grasp the cube cleanly without macro interference.
# ============================================================================

# ---- gripper gate (same proven settings) ------------------------------------
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
export ROLLOUT_CLOSE_ELBOW_FLEX_MAX="-49"
export ROLLOUT_CLOSE_WRIST_FLEX_MIN="101"

export ROLLOUT_Z_BIAS="6.0"
export ROLLOUT_Z_BIAS_TRIGGER="pose"
export ROLLOUT_Z_POSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_Z_POSE_ELBOW_FLEX_MAX="-47"
export ROLLOUT_Z_POSE_WRIST_FLEX_MIN="100"

# ---- NO after-grasp macro (pure ACT) -----------------------------------------
# Intentionally left unset — no ROLLOUT_AFTER_GRASP_MACRO.
# ACT policy runs freely: approach → grasp → whatever it decides next.

# ---- joint delta limiting (safety) -------------------------------------------
export ROLLOUT_MAX_DELTA_SHOULDER_PAN="1.0"
export ROLLOUT_MAX_DELTA_SHOULDER_LIFT="1.0"
export ROLLOUT_MAX_DELTA_ELBOW_FLEX="1.0"
export ROLLOUT_MAX_DELTA_WRIST_FLEX="1.5"
export ROLLOUT_MAX_DELTA_WRIST_ROLL="1.5"
export ROLLOUT_MAX_DELTA_GRIPPER="10.0"

# ---- rollout config ----------------------------------------------------------
export ROLLOUT_TASK="Pick up the visible purple cube. PURE ACT — no after-grasp macro, no visual servo. DRY RUN."
export ROLLOUT_DURATION="10"

export ROLLOUT_DEBUG_AFTER_GRASP_MACRO="0"
export ROLLOUT_DEBUG_ACTION="0"
export ROLLOUT_LOG_SUFFIX="_v2_100k_pure_act_pickup_dryrun"
export ROLLOUT_ACTION_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_pure_act_pickup_dryrun.csv"

rm -f "$ROLLOUT_ACTION_LOG_PATH"
/usr/bin/bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh 100000
