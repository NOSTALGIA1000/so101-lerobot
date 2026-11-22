#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="/home/nostalgia/lerobot_outputs/rollouts"
LOG_FILE="$LOG_DIR/act_sim_004000_nocube_mrt015_latest.log"
POLICY="/home/nostalgia/lerobot_outputs/act_sim_cube_until_2130/checkpoints/004000/pretrained_model"

mkdir -p "$LOG_DIR"
echo "log_file=$LOG_FILE"

set +e
printf '\n' | timeout --signal=INT 30s \
  /mnt/c/Users/ASUS/Documents/lerobot/wsl/rollout_act_sim_cube_safe.sh \
  "$POLICY" 172.28.48.1 0.15 3 \
  >"$LOG_FILE" 2>&1
status=$?
set -e

echo "exit_status=$status"
grep -aE 'Policy loaded|Robot connected|ZMQCamera|Rollout setup complete|control loop started|running slower|clamped|Rollout finished|disconnected|ERROR|Traceback|RuntimeError|EOFError' "$LOG_FILE" | tail -160 || true
echo "LOG_TAIL"
tail -80 "$LOG_FILE"
exit "$status"
