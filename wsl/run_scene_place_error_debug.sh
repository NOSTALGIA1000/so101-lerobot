#!/usr/bin/env bash
set -euo pipefail

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

python /mnt/c/Users/ASUS/Documents/lerobot/wsl/detect_scene_place_error_from_zmq.py \
  --seconds "${SCENE_PLACE_ERROR_SECONDS:-3}" \
  --out-dir "${SCENE_PLACE_ERROR_OUT_DIR:-/home/nostalgia/lerobot_outputs/rollouts/scene_place_error_debug_20260730}" \
  --csv-path "${SCENE_PLACE_ERROR_CSV:-/home/nostalgia/lerobot_outputs/rollouts/scene_place_error_debug_20260730.csv}"
