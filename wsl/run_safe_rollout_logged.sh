#!/usr/bin/env bash
set -euo pipefail

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

export FOLLOWER_PORT="${FOLLOWER_PORT:-/dev/ttyACM0}"

POLICY="${1:-/home/nostalgia/lerobot_outputs/act_cube_v1/checkpoints/050000/pretrained_model}"
CAMERA_SERVER="${2:-172.28.48.1}"
MAX_RELATIVE_TARGET="${3:-0.5}"
DURATION_S="${4:-8}"
LOG_DIR="${5:-/home/nostalgia/lerobot_outputs/rollouts}"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/rollout_$(date +%Y%m%d_%H%M%S)_ckpt$(basename "$(dirname "$POLICY")")_mrt${MAX_RELATIVE_TARGET}_dur${DURATION_S}.log"

echo "log_file=$LOG_FILE"
set +e
printf '\n' | timeout --signal=INT 45s \
  /mnt/c/Users/ASUS/Documents/lerobot/wsl/rollout_act_cube_safe.sh \
  "$POLICY" "$CAMERA_SERVER" "$MAX_RELATIVE_TARGET" "$DURATION_S" \
  >"$LOG_FILE" 2>&1
status=$?
set -e

echo "exit_status=$status"
echo "summary="
grep -aE 'Policy loaded|Robot connected|ZMQCamera|Rollout setup complete|control loop started|running slower|clamped|Rollout finished|disconnected|ERROR|Traceback|EOFError' "$LOG_FILE" | tail -120 || true
exit "$status"
