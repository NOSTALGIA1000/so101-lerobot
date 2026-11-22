#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Generic real-robot rollout runner for V4 (bottle place) / V5 (cap on cube).
# Pure ACT + safety delta clamp. No gates, no z-bias, no deepen, no servo.
# Borrowed the lerobot-rollout flags from run_v2_checkpoint_cube_10s_unlimited.sh.
#
# Usage: run_v4v5_checkpoint.sh v4|v5 STEP
#   STEP in {010000, 020000, 030000, 040000, 050000, last}
#   Optional env: ROLLOUT_TASK, ROLLOUT_DURATION, ROLLOUT_LOG_SUFFIX
# ============================================================================

MODEL="${1:?usage: run_v4v5_checkpoint.sh v4|v5 STEP}"
STEP="${2:?step required}"

# ---- path mapping (V4/V5 are nested one level deeper than V2) ----------------
case "$MODEL" in
  v4) TASK_DIR="act_bottle_place_v4" ;;
  v5) TASK_DIR="act_cap_on_cube_v5" ;;
  *)  echo "unknown model: $MODEL (expected v4|v5)" >&2; exit 2 ;;
esac

POLICY="/mnt/f/CC-project/lerobot-storage/outputs/real_test_candidates/act_${MODEL}_050000/${TASK_DIR}/checkpoints/${STEP}/pretrained_model"
if [[ -d "$POLICY" ]]; then
  echo "[OK] Policy checkpoint: $POLICY"
else
  echo "[FAIL] Checkpoint NOT FOUND: $POLICY" >&2
  exit 2
fi

if [[ -c /dev/ttyACM0 ]]; then
  echo "[OK] Follower device: /dev/ttyACM0"
else
  echo "[FAIL] Follower device /dev/ttyACM0 NOT FOUND" >&2
  exit 2
fi

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

LOG_DIR="$HOME/lerobot_outputs/rollouts"
mkdir -p "$LOG_DIR"
SUFFIX="${ROLLOUT_LOG_SUFFIX:-}"
LOG_BASENAME="${MODEL}_${STEP}_pure${SUFFIX}"
LOG_FILE="$LOG_DIR/${LOG_BASENAME}.log"

# ---- pure ACT: NO delta clamp (user: 限幅会失真), everything else off -------
# ROLLOUT_MAX_DELTA_* left unset = fully disabled, ACT output passed through.
# Re-enable only for jitter/爆冲 troubleshooting:
#   export ROLLOUT_MAX_DELTA_SHOULDER_PAN="2.0"
#   export ROLLOUT_MAX_DELTA_SHOULDER_LIFT="1.0"
#   export ROLLOUT_MAX_DELTA_ELBOW_FLEX="2.0"
#   export ROLLOUT_MAX_DELTA_WRIST_FLEX="1.5"
#   export ROLLOUT_MAX_DELTA_WRIST_ROLL="1.5"
#   export ROLLOUT_MAX_DELTA_GRIPPER="10.0"

# explicitly disable assist features (guard against env leakage)
export ROLLOUT_GRIPPER_TIMING_GATE=""
export ROLLOUT_AFTER_GRASP_MACRO=""
export ROLLOUT_Z_BIAS="0"
export ROLLOUT_WRIST_GRASP_ENABLE="0"
export ROLLOUT_SCENE_GRASP_ENABLE="0"
export ROLLOUT_SCENE_SERVO_DRY_RUN="1"   # visual servo off (not enabled anyway)

if [[ "$MODEL" = v4 ]]; then
  ROLLOUT_TASK="${ROLLOUT_TASK:-Pick up the visible bottle, carry it to the target zone, release it inside. Pure ACT.}"
else
  ROLLOUT_TASK="${ROLLOUT_TASK:-Pick up the visible cap, place it precisely on top of the cube. Pure ACT.}"
fi
# 15s proved too short (trial7 place truncated); 20s lets place+release complete
ROLLOUT_DURATION="${ROLLOUT_DURATION:-20}"
# max_rel=5.0: 3.0 clamped shoulder_lift so bottle could not be lifted (trial4 vs trial5)
ROLLOUT_MAX_RELATIVE_TARGET="${ROLLOUT_MAX_RELATIVE_TARGET:-5.0}"

export ROLLOUT_ACTION_LOG_PATH="$LOG_DIR/${LOG_BASENAME}.csv"
rm -f "$ROLLOUT_ACTION_LOG_PATH"

echo "=== ${MODEL^^} ${STEP} PURE ACT rollout ==="
echo "  task:     $ROLLOUT_TASK"
echo "  duration: ${ROLLOUT_DURATION}s"
echo "  max_rel:  ${ROLLOUT_MAX_RELATIVE_TARGET}"
echo "  log:      $LOG_FILE"
echo "  action:   $ROLLOUT_ACTION_LOG_PATH"
echo ""

timeout --signal=INT 90s \
  lerobot-rollout \
    --strategy.type=base \
    --policy.path="$POLICY" \
    --device=cuda \
    --fps=30 \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=R12260101 \
    --robot.max_relative_target="$ROLLOUT_MAX_RELATIVE_TARGET" \
    --robot.cameras="{wrist: {type: zmq, server_address: 172.28.48.1, port: 5555, camera_name: wrist, width: 640, height: 480, fps: 30}, scene: {type: zmq, server_address: 172.28.48.1, port: 5555, camera_name: scene, width: 640, height: 480, fps: 30}}" \
    --rename_map='{"observation.images.scene": "observation.images.overhead"}' \
    --task="$ROLLOUT_TASK" \
    --duration="$ROLLOUT_DURATION" \
    --display_data=false \
    >"$LOG_FILE" 2>&1

status=$?
echo "exit_status=$status"
echo "policy=$POLICY"
echo "log=$LOG_FILE"
grep -aE 'ERROR|Traceback|RuntimeError|EOFError|Duration limit|disconnected' "$LOG_FILE" | tail -20 || true
echo "---LOG_TAIL---"
tail -40 "$LOG_FILE"
exit "$status"
