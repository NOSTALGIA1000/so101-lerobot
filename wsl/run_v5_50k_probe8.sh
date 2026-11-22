#!/usr/bin/env bash
set -euo pipefail

# V5 50K first-contact probe: short pure-ACT rollout for real-robot sanity.

export ROLLOUT_DURATION="${ROLLOUT_DURATION:-8}"
export ROLLOUT_LOG_SUFFIX="${ROLLOUT_LOG_SUFFIX:-_probe8}"

exec bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v5_50k_pure.sh
