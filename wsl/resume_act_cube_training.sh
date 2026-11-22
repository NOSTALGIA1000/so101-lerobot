#!/usr/bin/env bash
set -euo pipefail

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

export PATH="/usr/lib/wsl/lib:$PATH"
export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false

CHECKPOINT="${1:-$HOME/lerobot_outputs/act_cube_v1/checkpoints/020000}"
CONFIG_PATH="$CHECKPOINT/pretrained_model/train_config.json"

cd "$HOME/lerobot_workspace/lerobot"
exec lerobot-train --config_path="$CONFIG_PATH" --resume=true
