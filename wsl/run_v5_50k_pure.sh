#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# V5 (cap -> cube top) 50K pure-ACT rollout.
# ============================================================================

echo "=== V5 050000 PURE ACT ==="
echo "  Task: pick up cap, place precisely on top of cube."

export ROLLOUT_TASK="Pick up the visible cap, place it precisely on top of the cube. Pure ACT."
export ROLLOUT_DURATION="${ROLLOUT_DURATION:-20}"
export ROLLOUT_LOG_SUFFIX="${ROLLOUT_LOG_SUFFIX:-_v5_50k}"
export ROLLOUT_AUTO_CONFIRM=1

echo "  Duration: ${ROLLOUT_DURATION}s"
echo ""
if [[ "${ROLLOUT_AUTO_CONFIRM:-0}" = "1" ]]; then
  echo "Auto-confirm enabled by ROLLOUT_AUTO_CONFIRM=1."
else
  echo "Press ENTER to start, or Ctrl+C to abort..."
  read -r _
fi

exec bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v4v5_checkpoint.sh v5 050000
