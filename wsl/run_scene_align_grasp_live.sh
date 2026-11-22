#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Scene camera alignment grasp + visual servo place — LIVE
# ============================================================================
# Flow:
#   PICK(ACT) → pose_ok → scene align pan → GRASP → deepen → lift → SERVO → RELEASE
#
# Scene camera detects cube X position, micro-adjusts shoulder_pan to centre
# cube under gripper before closing. Compensates for ACT generalisation gaps
# (cube moved 1-2 cm after failed first attempt).
# ============================================================================

echo "=============================================="
echo " SCENE ALIGN GRASP + SERVO PLACE — LIVE"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="
echo ""

STEP=100000
POLICY="/mnt/f/CC-project/lerobot-storage/outputs/real_test_candidates/act_v2_050000/checkpoints-V2/${STEP}/pretrained_model"
if [[ -d "$POLICY" ]]; then
    echo "[OK] Policy checkpoint: $POLICY"
else
    echo "[FAIL] Policy checkpoint NOT FOUND: $POLICY"
    exit 2
fi

if [[ -c /dev/ttyACM0 ]]; then
    echo "[OK] Follower device: /dev/ttyACM0"
else
    echo "[FAIL] Follower device /dev/ttyACM0 NOT FOUND"
    exit 2
fi

echo -n "[..] Checking camera bridge... "
source "$HOME/miniconda3/etc/profile.d/conda.sh" 2>/dev/null || true
conda activate lerobot 2>/dev/null || true
BRIDGE_OK=$(python3 /mnt/c/Users/ASUS/Documents/lerobot/wsl/preflight_check.py 2>&1)
if [[ $? -eq 0 ]]; then
    echo "[OK]"
else
    echo "[FAIL]"
    echo "$BRIDGE_OK"
    exit 2
fi

echo ""

# ---- gripper timing gate (same proven close gate) ---------------------------
export ROLLOUT_GRIPPER_TIMING_GATE="open_then_close_intent"
export ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN="0"
export ROLLOUT_GRIPPER_OPEN_VALUE="45"
export ROLLOUT_GRIPPER_CLOSE_INTENT_MAX="10"
export ROLLOUT_GRIPPER_CLOSE_DELAY_HITS="0"
export ROLLOUT_CLOSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_CLOSE_ELBOW_FLEX_MAX="-54"
export ROLLOUT_CLOSE_WRIST_FLEX_MIN="101"

# ---- scene alignment (NEW) --------------------------------------------------
export ROLLOUT_SCENE_ALIGN_ENABLE="1"
export ROLLOUT_SCENE_ALIGN_DX_THRESHOLD="15"       # pixels — |cube_cx - centre| ≤ this = aligned
export ROLLOUT_SCENE_ALIGN_K_PAN="0.008"           # P-gain — pan_delta = K * (centre_x - cube_cx)
export ROLLOUT_SCENE_ALIGN_STABLE_FRAMES="5"       # consecutive aligned frames before close
export ROLLOUT_SCENE_ALIGN_MAX_STEPS="60"           # timeout (frames) if alignment never converges
export ROLLOUT_SCENE_ALIGN_MAX_PAN_DELTA="3.0"     # max pan adjustment per frame (degrees)
export ROLLOUT_SCENE_ALIGN_DEBUG="1"

# ---- after-grasp macro: visual servo place ----------------------------------
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

# ---- visual servo parameters ------------------------------------------------
export ROLLOUT_SCENE_SERVO_DRY_RUN="0"              # 0 = LIVE robot control
export ROLLOUT_SCENE_SERVO_DX_THRESHOLD="20"
export ROLLOUT_SCENE_SERVO_DY_THRESHOLD="20"
export ROLLOUT_SCENE_SERVO_STABLE_FRAMES="10"
export ROLLOUT_SCENE_SERVO_K_PAN="0.01"
export ROLLOUT_SCENE_SERVO_K_ELBOW="-0.006"
export ROLLOUT_SCENE_SERVO_MAX_STEPS="300"
export ROLLOUT_SCENE_SERVO_LOG_DIR="$HOME/lerobot_outputs/rollouts/scene_servo_debug"
export ROLLOUT_SCENE_SERVO_SAVE_EVERY="5"

# ---- release ----------------------------------------------------------------
export ROLLOUT_SCENE_SERVO_LOWER_FRAMES="30"

# ---- joint delta limiting ---------------------------------------------------
export ROLLOUT_MAX_DELTA_SHOULDER_PAN="2.0"
export ROLLOUT_MAX_DELTA_SHOULDER_LIFT="2.0"
export ROLLOUT_MAX_DELTA_ELBOW_FLEX="2.0"
export ROLLOUT_MAX_DELTA_WRIST_FLEX="1.5"
export ROLLOUT_MAX_DELTA_WRIST_ROLL="1.5"
export ROLLOUT_MAX_DELTA_GRIPPER="10.0"

# ---- disable other assist features ------------------------------------------
export ROLLOUT_WRIST_GRASP_ENABLE="0"
export ROLLOUT_SCENE_GRASP_ENABLE="0"
unset ROLLOUT_Z_BIAS || true
unset ROLLOUT_ELBOW_BIAS || true
unset ROLLOUT_GRIPPER_CLOSE_LATCH || true

# ---- rollout config ---------------------------------------------------------
export ROLLOUT_TASK="Scene-align grasp + visual servo place: ACT approach, scene camera centres pan over cube, close, deepen, lift, servo to target."
export ROLLOUT_DURATION="30"
export ROLLOUT_DEBUG_AFTER_GRASP_MACRO="1"
export ROLLOUT_DEBUG_ACTION="0"
export ROLLOUT_LOG_SUFFIX="_scene_align_live"
export ROLLOUT_ACTION_LOG_PATH="$HOME/lerobot_outputs/rollouts/scene_align_live.csv"

echo "----------------------------------------------"
echo " SCENE ALIGNMENT GRASP"
echo "----------------------------------------------"
echo "  align enable:       ${ROLLOUT_SCENE_ALIGN_ENABLE}"
echo "  dx threshold:       ${ROLLOUT_SCENE_ALIGN_DX_THRESHOLD} px"
echo "  K_pan:              ${ROLLOUT_SCENE_ALIGN_K_PAN}"
echo "  stable frames:      ${ROLLOUT_SCENE_ALIGN_STABLE_FRAMES}"
echo "  max steps:          ${ROLLOUT_SCENE_ALIGN_MAX_STEPS}"
echo "  max pan delta/frame: ${ROLLOUT_SCENE_ALIGN_MAX_PAN_DELTA}°"
echo "  debug:              ${ROLLOUT_SCENE_ALIGN_DEBUG}"
echo ""
echo "  close gate:         elbow ≤ -54, delay 0 hits"
echo "  after-grasp:        visual_servo_place"
echo "  duration:           30s"
echo "----------------------------------------------"
echo ""
echo "Press ENTER to start, or Ctrl+C to abort..."
read -r _

rm -f "$ROLLOUT_ACTION_LOG_PATH"
/usr/bin/bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh ${STEP}
