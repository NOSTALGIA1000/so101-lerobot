#!/usr/bin/env bash
set -euo pipefail

STEP="${1:?usage: run_v2_checkpoint_cube_10s_unlimited.sh 030000|040000|050000|060000|070000|080000|090000|100000}"

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

LOG_DIR="$HOME/lerobot_outputs/rollouts"
mkdir -p "$LOG_DIR"
LOG_SUFFIX="${ROLLOUT_LOG_SUFFIX:-}"
LOG_FILE="$LOG_DIR/v2_${STEP}_cube_10s_unlimited${LOG_SUFFIX}.log"

POLICY_ROOT="/mnt/f/CC-project/lerobot-storage/outputs/real_test_candidates/act_v2_050000"
if [[ -d "$POLICY_ROOT/checkpoints-V2/${STEP}/pretrained_model" ]]; then
  POLICY="$POLICY_ROOT/checkpoints-V2/${STEP}/pretrained_model"
elif [[ -d "$POLICY_ROOT/checkpoints/${STEP}/pretrained_model" ]]; then
  POLICY="$POLICY_ROOT/checkpoints/${STEP}/pretrained_model"
else
  echo "Missing V2 checkpoint: $STEP" >&2
  echo "Checked:" >&2
  echo "  $POLICY_ROOT/checkpoints-V2/${STEP}/pretrained_model" >&2
  echo "  $POLICY_ROOT/checkpoints/${STEP}/pretrained_model" >&2
  exit 2
fi

ROLLOUT_TASK="${ROLLOUT_TASK:-Pick up the cube from the table, lift it, move it to the white target zone, and release it.}"
ROLLOUT_DURATION="${ROLLOUT_DURATION:-20}"

# Disable workspace joint soft-bounds latch entirely (entry elbow far below
# physical range, so it can never trigger). Pure ACT keeps full joint freedom.
export ROLLOUT_WORKSPACE_ENTRY_ELBOW=-999

timeout --signal=INT 90s \
  lerobot-rollout \
    --strategy.type=base \
    --policy.path="$POLICY" \
    --device=cuda \
    --fps=30 \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=R12260101 \
    --robot.cameras="{wrist: {type: zmq, server_address: 172.28.48.1, port: 5555, camera_name: wrist, width: 640, height: 480, fps: 30}, scene: {type: zmq, server_address: 172.28.48.1, port: 5555, camera_name: scene, width: 640, height: 480, fps: 30}}" \
    --rename_map='{"observation.images.scene": "observation.images.overhead"}' \
    --task="$ROLLOUT_TASK" \
    --duration="$ROLLOUT_DURATION" \
    --display_data=false \
    >"$LOG_FILE" 2>&1

status=$?
echo "exit_status=$status"
echo "step=$STEP"
echo "log=$LOG_FILE"
grep -aE 'Policy loaded|Robot connected|ZMQCamera|Rollout setup complete|control loop started|running slower|clamped|Duration limit reached|Rollout finished|disconnected|ERROR|Traceback|RuntimeError|EOFError' "$LOG_FILE" | tail -120 || true
echo "---LOG_TAIL---"
tail -80 "$LOG_FILE"
exit "$status"
