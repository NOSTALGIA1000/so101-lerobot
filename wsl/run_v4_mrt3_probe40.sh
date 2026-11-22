#!/usr/bin/env bash
set -euo pipefail
export ROLLOUT_AUTO_CONFIRM=1
export ROLLOUT_DURATION=40
export ROLLOUT_MAX_RELATIVE_TARGET=3.0
export ROLLOUT_LOG_SUFFIX=_mrt3_probe40
bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v4_50k_pure.sh