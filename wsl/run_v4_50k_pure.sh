#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# V4 (bottle -> target zone) 50K pure-ACT rollout.
# ============================================================================

echo "=== V4 050000 PURE ACT ==="
echo "  Task: pick up bottle, carry to target zone, release inside."

export ROLLOUT_TASK="Pick up the visible bottle, carry it to the target zone, release it inside. Pure ACT."
export ROLLOUT_DURATION="${ROLLOUT_DURATION:-20}"
export ROLLOUT_LOG_SUFFIX="${ROLLOUT_LOG_SUFFIX:-_v4_50k}"

echo "  Duration: ${ROLLOUT_DURATION}s"
echo ""
if [[ "${ROLLOUT_AUTO_CONFIRM:-0}" = "1" ]]; then
  echo "Auto-confirm enabled by ROLLOUT_AUTO_CONFIRM=1."
else
  echo "Press ENTER to start, or Ctrl+C to abort..."
  read -r _
fi

exec bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v4v5_checkpoint.sh v4 050000
