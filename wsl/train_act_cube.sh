#!/usr/bin/env bash
set -euo pipefail

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

export PATH="/usr/lib/wsl/lib:$PATH"
export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false

dataset_root="$HOME/lerobot_data/so101_grasp_cube_test_20260721_200217"
output_dir="${OUTPUT_DIR:-$HOME/lerobot_outputs/act_cube_v1}"
batch_size="${BATCH_SIZE:-4}"
steps="${STEPS:-50000}"

mkdir -p "$(dirname "$output_dir")"

exec lerobot-train \
  --dataset.repo_id=local/so101_grasp_cube_test_20260721_200217 \
  --dataset.root="$dataset_root" \
  --dataset.eval_split=0.1 \
  --policy.type=act \
  --policy.device=cuda \
  --policy.use_amp=true \
  --policy.push_to_hub=false \
  --output_dir="$output_dir" \
  --job_name=act_cube_v1 \
  --batch_size="$batch_size" \
  --num_workers=4 \
  --steps="$steps" \
  --eval_steps=1000 \
  --max_eval_samples=1024 \
  --env_eval_freq=0 \
  --save_freq=5000 \
  --log_freq=100 \
  --seed=1000 \
  --wandb.enable=false
