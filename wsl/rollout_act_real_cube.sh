#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# Cube Contact Rollout (Real-Data Fine-Tuned ACT)
# ============================================================
# Runs fine-tuned ACT policy WITH cube on table.
# Strict safety: max_relative_target=0.05, duration=5s.
# Only run after no-cube test passes.
# Camera: 64x64 (matches fine-tune resolution).
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/project_config.sh"

source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

POLICY="${1:-$OUTPUT_ROOT/act_real_finetune_sim018K_lr1e-5_20260723/checkpoints/010000/pretrained_model}"
MAX_REL_TARGET="${2:-0.05}"
DURATION_S="${3:-5}"

export ROLLOUT_TASK="${ROLLOUT_TASK:-Small real-robot cube grasp test. Approach the visible cube slowly, align the gripper, gently close on the cube. Do not lift or place.}"

LOG_DIR="$OUTPUT_ROOT/rollouts"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/act_real_cube_mrt$(echo "$MAX_REL_TARGET" | tr -d '.')_latest.log"

echo "============================================================"
echo "Real-Data ACT Rollout: CUBE CONTACT Test"
echo "============================================================"
echo "  policy:       $POLICY"
echo "  camera:       $CAMERA_SERVER:5555"
echo "  follower:     $FOLLOWER_PORT"
echo "  max_rel_target: $MAX_REL_TARGET (STRICT)"
echo "  duration:     ${DURATION_S}s"
echo "  log:          $LOG_FILE"
echo ""
echo "  PREREQUISITES:"
echo "    1. no-cube rollout PASSED"
echo "    2. Cube on table in workspace"
echo "    3. Physical E-stop accessible"
echo "============================================================"

if [[ ! -d "$POLICY" ]]; then
    echo "ERROR: Policy checkpoint not found: $POLICY" >&2
    exit 1
fi

read -rp "Confirm: cube on table, E-stop ready, no-cube test passed? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted."
    exit 1
fi

set +e
timeout --signal=INT "${DURATION_S}s" \
  lerobot-rollout \
    --strategy.type=base \
    --policy.path="$POLICY" \
    --device=cuda \
    --fps=30 \
    --robot.type=so101_follower \
    --robot.port="$FOLLOWER_PORT" \
    --robot.id="$ROBOT_ID" \
    --robot.max_relative_target="$MAX_REL_TARGET" \
    --robot.cameras="{wrist: {type: zmq, server_address: $CAMERA_SERVER, port: 5555, camera_name: wrist, width: 64, height: 64, fps: 30}, scene: {type: zmq, server_address: $CAMERA_SERVER, port: 5555, camera_name: scene, width: 64, height: 64, fps: 30}}" \
    --task="$ROLLOUT_TASK" \
    --duration="$DURATION_S" \
    --display_data=false \
    >"$LOG_FILE" 2>&1
status=$?
set -e

echo "exit_status=$status"
grep -aE 'Policy loaded|Robot connected|ZMQCamera|Rollout setup complete|control loop started|running slower|clamped|Duration limit reached|Rollout finished|disconnected|ERROR|Traceback|RuntimeError|EOFError' "$LOG_FILE" | tail -80 || true
echo "--- LOG_TAIL ---"
tail -40 "$LOG_FILE"

if [[ $status -eq 0 ]]; then
    echo "ROLLOUT_RESULT=PASS"
else
    echo "ROLLOUT_RESULT=FAIL (exit=$status)"
fi
exit "$status"
