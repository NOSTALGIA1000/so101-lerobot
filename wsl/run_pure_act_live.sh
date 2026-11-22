#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Pure ACT rollout — minimal close gate, no alignment, no macro.
# ACT controls everything. Relaxed elbow threshold for earlier grasp.
# ============================================================================

echo "=============================================="
echo " PURE ACT LIVE ROLLOUT (elbow <= -50)"
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

# ---- minimal gate: delay first close until arm is deep enough ----------------
export ROLLOUT_GRIPPER_TIMING_GATE="open_then_close_intent"
export ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN="0"
export ROLLOUT_GRIPPER_OPEN_VALUE="45"
export ROLLOUT_GRIPPER_CLOSE_INTENT_MAX="10"
export ROLLOUT_GRIPPER_CLOSE_DELAY_HITS="0"
export ROLLOUT_CLOSE_SHOULDER_LIFT_MIN="30"
export ROLLOUT_CLOSE_ELBOW_FLEX_MAX="-50"    # relaxed from -54 → earlier grasp
export ROLLOUT_CLOSE_WRIST_FLEX_MIN="101"

# ---- disable all assist features ---------------------------------------------
export ROLLOUT_WRIST_GRASP_ENABLE="0"
export ROLLOUT_SCENE_GRASP_ENABLE="0"

# ---- joint delta limiting (disabled — pure ACT, let policy drive) -----------
# export ROLLOUT_MAX_DELTA_SHOULDER_PAN="2.0"
# export ROLLOUT_MAX_DELTA_SHOULDER_LIFT="2.0"
# export ROLLOUT_MAX_DELTA_ELBOW_FLEX="2.0"
# export ROLLOUT_MAX_DELTA_WRIST_FLEX="1.5"
# export ROLLOUT_MAX_DELTA_WRIST_ROLL="1.5"
# export ROLLOUT_MAX_DELTA_GRIPPER="10.0"

# ---- rollout config ---------------------------------------------------------
export ROLLOUT_TASK="Pure ACT: grab the purple cube naturally. Elbow <= -50 close gate."
export ROLLOUT_DURATION="15"
export ROLLOUT_DEBUG_AFTER_GRASP_MACRO="0"
export ROLLOUT_DEBUG_ACTION="0"

echo "----------------------------------------------"
echo " PURE ACT MODE"
echo "----------------------------------------------"
echo "  Close gate: elbow <= -50 (relaxed from -54)"
echo "  Delay hits: 0 → close immediately on intent"
echo "  No latch — ACT can retry"
echo "  ACT controls gripper amplitude"
echo "  Duration: 15s"
echo "----------------------------------------------"
echo ""
echo "Press ENTER to start, or Ctrl+C to abort..."
read -r _

rm -f "$HOME/lerobot_outputs/rollouts/v2_100000_cube_10s_unlimited.log"
/usr/bin/bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_checkpoint_cube_10s_unlimited.sh ${STEP}
