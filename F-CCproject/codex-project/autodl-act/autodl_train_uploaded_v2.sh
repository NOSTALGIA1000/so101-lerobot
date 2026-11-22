#!/bin/bash
set -euo pipefail

export HF_HOME=/root/autodl-tmp/huggingface
export HF_LEROBOT_HOME=/root/autodl-tmp/huggingface/lerobot
export WANDB_MODE=disabled
export PYTHONPATH=/root/lerobot_workspace/lerobot/src:${PYTHONPATH:-}

cd /root/lerobot_workspace/lerobot
mkdir -p /root/autodl-tmp/lerobot_outputs

DATASET_ROOT=/root/autodl-tmp/huggingface/lerobot/so101_cube_pick_place_v2
OUT=/root/autodl-tmp/lerobot_outputs/act_cube_pick_place_v2_uploaded
LOG=/root/autodl-tmp/lerobot_outputs/act_cube_pick_place_v2_uploaded_train.log

test -d "$DATASET_ROOT/meta"
test -d "$DATASET_ROOT/data"
test -d "$DATASET_ROOT/videos"

python -m lerobot.scripts.lerobot_train \
  --dataset.repo_id=RItcheOhe/so101_cube_pick_place_v2 \
  --dataset.root="$DATASET_ROOT" \
  --policy.type=act \
  --policy.push_to_hub=false \
  --output_dir="$OUT" \
  --batch_size=32 \
  --steps=100000 \
  --save_freq=10000 \
  --num_workers=8 2>&1 | tee "$LOG"
