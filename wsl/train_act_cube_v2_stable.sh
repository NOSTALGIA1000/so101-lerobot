#!/usr/bin/env bash
set -euo pipefail

# Lower-pressure ACT training profile for WSL stability.
# Use this for the next v2 dataset/retrain, not for the already completed v1 run.

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

export PATH="/usr/lib/wsl/lib:$PATH"
export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-4}"

DATASET_ROOT="${DATASET_ROOT:-$HOME/lerobot_data/so101_grasp_cube_test_20260721_200217}"
OUTPUT_DIR="${OUTPUT_DIR:-$HOME/lerobot_outputs/act_cube_v2_stable}"
REPO_ID="${REPO_ID:-local/so101_grasp_cube_test_20260721_200217}"

cd "$HOME/lerobot_workspace/lerobot"

exec nice -n 10 lerobot-train \
  --dataset.repo_id="$REPO_ID" \
  --dataset.root="$DATASET_ROOT" \
  --dataset.eval_split=0.1 \
  --policy.type=act \
  --policy.device=cuda \
  --policy.use_amp=true \
  --batch_size=2 \
  --num_workers=2 \
  --prefetch_factor=2 \
  --persistent_workers=false \
  --steps=50000 \
  --eval_steps=2000 \
  --max_eval_samples=512 \
  --save_freq=10000 \
  --log_freq=100 \
  --seed=1000 \
  --output_dir="$OUTPUT_DIR" \
  --job_name=act_cube_v2_stable \
  --wandb.enable=false \
  --policy.push_to_hub=false
