#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# V2 100K + visual servo place — LIVE (robot control enabled)
# ============================================================================
# WARNING: Robot will move. Ensure arm has clearance before running.
#
# Flow: STATE_PICK → STATE_GRASP → STATE_LIFT → STATE_SERVO → STATE_RELEASE
#
# Tuning order if place fails:
#   - Increase K_PAN / K_ELBOW (0.003/0.002 → 0.005/0.004 → 0.008/0.006)
#   - Relax thresholds if servo oscillates (20 → 30 → 40)
#   - Increase MAX_STEPS if servo times out before converging
# ============================================================================

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================
echo "=============================================="
echo " SO-101 VISUAL SERVO LIVE ROLLOUT"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="
echo ""

# -- checkpoint --
STEP=100000
POLICY="/mnt/f/CC-project/lerobot-storage/outputs/real_test_candidates/act_v2_050000/checkpoints-V2/${STEP}/pretrained_model"
if [[ -d "$POLICY" ]]; then
    echo "[OK] Policy checkpoint: $POLICY"
else
    echo "[FAIL] Policy checkpoint NOT FOUND: $POLICY"
    exit 2
fi

# -- follower device --
if [[ -c /dev/ttyACM0 ]]; then
    echo "[OK] Follower device: /dev/ttyACM0 ($(ls -l /dev/ttyACM0 | awk '{print $NF}'))"
else
    echo "[FAIL] Follower device /dev/ttyACM0 NOT FOUND"
    exit 2
fi

# -- camera bridge --
echo -n "[..] Checking camera bridge + core.py... "
source "$HOME/miniconda3/etc/profile.d/conda.sh" 2>/dev/null || true
conda activate lerobot 2>/dev/null || true
BRIDGE_OK=$(python3 /mnt/c/Users/ASUS/Documents/lerobot/wsl/preflight_check.py 2>&1)
if [[ $? -eq 0 ]]; then
    echo "[OK]"
    echo "$BRIDGE_OK" | while read line; do echo "       $line"; done
else
    echo "[FAIL]"
    echo "$BRIDGE_OK"
    echo "       Run: start_camera_bridge_two.ps1 on Windows"
    exit 2
fi

echo ""

# ============================================================================
# ROLLOUT PARAMETERS
# ============================================================================
echo "----------------------------------------------"
echo " KEY PARAMETERS"
echo "----------------------------------------------"

# ---- gripper / Z-bias ------------------------------------------------------
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

echo "  gripper gate:        ${ROLLOUT_GRIPPER_TIMING_GATE}"
echo "  gripper open value:  ${ROLLOUT_GRIPPER_OPEN_VALUE}"
echo "  gripper close intent:<= ${ROLLOUT_GRIPPER_CLOSE_INTENT_MAX}"
echo "  close delay hits:    ${ROLLOUT_GRIPPER_CLOSE_DELAY_HITS}"
echo "  Z-bias:              ${ROLLOUT_Z_BIAS} deg (trigger=${ROLLOUT_Z_BIAS_TRIGGER})"
echo "  elbow bias:          ${ROLLOUT_ELBOW_BIAS} deg (trigger=${ROLLOUT_ELBOW_BIAS_TRIGGER})  [neg=deeper]"

# ---- after-grasp macro -----------------------------------------------------
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

echo "  macro hold frames:   ${ROLLOUT_AFTER_GRASP_HOLD_FRAMES}"
echo "  macro lift frames:   ${ROLLOUT_AFTER_GRASP_LIFT_FRAMES}"
echo "  lift target:         SL=28  EF=-40  WF=101"

# ---- visual servo parameters -----------------------------------------------
export ROLLOUT_SCENE_SERVO_DRY_RUN="0"          # 0 = LIVE robot control
export ROLLOUT_SCENE_SERVO_DX_THRESHOLD="20"
export ROLLOUT_SCENE_SERVO_DY_THRESHOLD="20"
export ROLLOUT_SCENE_SERVO_STABLE_FRAMES="10"
export ROLLOUT_SCENE_SERVO_K_PAN="0.01"
export ROLLOUT_SCENE_SERVO_K_ELBOW="-0.006"
export ROLLOUT_SCENE_SERVO_MAX_STEPS="300"
export ROLLOUT_SCENE_SERVO_LOG_DIR="$HOME/lerobot_outputs/rollouts/scene_servo_debug"
export ROLLOUT_SCENE_SERVO_SAVE_EVERY="5"

echo "  DRY_RUN:             ${ROLLOUT_SCENE_SERVO_DRY_RUN} (0=LIVE!)"
echo "  k_pan:               ${ROLLOUT_SCENE_SERVO_K_PAN}"
echo "  k_elbow:             ${ROLLOUT_SCENE_SERVO_K_ELBOW}"
echo "  servo threshold:     |dx|<${ROLLOUT_SCENE_SERVO_DX_THRESHOLD}  |dy|<${ROLLOUT_SCENE_SERVO_DY_THRESHOLD}"
echo "  stable frames:       ${ROLLOUT_SCENE_SERVO_STABLE_FRAMES}"
echo "  max servo steps:     ${ROLLOUT_SCENE_SERVO_MAX_STEPS}"

# ---- release ----------------------------------------------------------------
export ROLLOUT_SCENE_SERVO_LOWER_FRAMES="30"

echo "  release lower frames: ${ROLLOUT_SCENE_SERVO_LOWER_FRAMES}"

# ---- joint delta limiting ---------------------------------------------------
export ROLLOUT_MAX_DELTA_SHOULDER_PAN="2.0"
export ROLLOUT_MAX_DELTA_SHOULDER_LIFT="2.0"
export ROLLOUT_MAX_DELTA_ELBOW_FLEX="2.0"
export ROLLOUT_MAX_DELTA_WRIST_FLEX="1.5"
export ROLLOUT_MAX_DELTA_WRIST_ROLL="1.5"
export ROLLOUT_MAX_DELTA_GRIPPER="10.0"

echo "  delta limit (deg/f): SP=2.0  SL=2.0  EF=2.0  WF=1.5  WR=1.5  GR=10"

# ---- rollout config ---------------------------------------------------------
export ROLLOUT_TASK="Pick up the visible purple cube, lift it, then use scene camera visual servo to place it on the white target. LIVE — robot moves."
export ROLLOUT_DURATION="30"

echo "  duration:            ${ROLLOUT_DURATION}s"
echo "  fps:                 30"

export ROLLOUT_DEBUG_AFTER_GRASP_MACRO="1"
export ROLLOUT_DEBUG_ACTION="0"
export ROLLOUT_LOG_SUFFIX="_v2_100k_scene_servo_live"
export ROLLOUT_ACTION_LOG_PATH="$HOME/lerobot_outputs/rollouts/v2_100000_scene_servo_live.csv"

echo ""
echo "----------------------------------------------"
echo " STATE MACHINE:"
echo "   STATE_PICK  → ACT approach cube"
echo "   STATE_GRASP → gripper closes, hold clamp pose"
echo "   STATE_LIFT  → lift cube to clear table"
echo "   STATE_SERVO → scene camera P-controller align"
echo "   STATE_RELEASE → lower arm, open gripper, place"
echo "----------------------------------------------"
echo ""
echo "=============================================="
echo " READY TO START LIVE ROLLOUT"
echo "=============================================="
echo ""
echo "Press ENTER to start, or Ctrl+C to abort..."
read -r _

# ============================================================================
# RUN
# ============================================================================
rm -f "$ROLLOUT_ACTION_LOG_PATH"
/usr/bin/bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh ${STEP}
