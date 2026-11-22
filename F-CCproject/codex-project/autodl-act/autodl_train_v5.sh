#!/bin/bash
set -euo pipefail

export HF_HOME=/root/autodl-tmp/hf
export HF_LEROBOT_HOME=/root/autodl-tmp/lerobot
export WANDB_MODE=disabled
export PYTHONPATH=/root/lerobot_workspace/lerobot/src:${PYTHONPATH:-}

mkdir -p /root/autodl-tmp/lerobot_outputs
cd /root/lerobot_workspace/lerobot

OUT=/root/autodl-tmp/lerobot_outputs/act_cap_on_cube_v5_all
LOG=/root/autodl-tmp/lerobot_outputs/act_cap_on_cube_v5_all_train.log

python -m lerobot.scripts.lerobot_train \
  --dataset.repo_id=RItcheOhe/so101_cap_on_cube_v5_all \
  --policy.type=act \
  --policy.push_to_hub=false \
  --output_dir="$OUT" \
  --batch_size=32 \
  --steps=50000 \
  --save_freq=10000 \
  --num_workers=8 2>&1 | tee "$LOG"

