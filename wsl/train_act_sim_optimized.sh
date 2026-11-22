#!/usr/bin/env bash
set -euo pipefail

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

export PATH="/usr/lib/wsl/lib:$PATH"
export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-2}"

DATASET_ROOT="${DATASET_ROOT:-$HOME/lerobot_data/so101_sim_cube_pick_img64}"
REPO_ID="${REPO_ID:-local/so101_sim_cube_pick_img64}"
OUTPUT_DIR="${OUTPUT_DIR:-$HOME/lerobot_outputs/act_sim_cube_optimized_20260723}"
STEPS="${STEPS:-20000}"
BATCH_SIZE="${BATCH_SIZE:-2}"
NUM_WORKERS="${NUM_WORKERS:-2}"
EVAL_STEPS="${EVAL_STEPS:-1000}"
SAVE_FREQ="${SAVE_FREQ:-1000}"
LOG_FREQ="${LOG_FREQ:-50}"
SEED="${SEED:-20260723}"

cd "$HOME/lerobot_workspace/lerobot"

exec nice -n 10 lerobot-train \
  --dataset.repo_id="$REPO_ID" \
  --dataset.root="$DATASET_ROOT" \
  --dataset.eval_split=0.1 \
  --policy.type=act \
  --policy.device=cuda \
  --policy.use_amp=true \
  --batch_size="$BATCH_SIZE" \
  --num_workers="$NUM_WORKERS" \
  --prefetch_factor=2 \
  --persistent_workers=false \
  --steps="$STEPS" \
  --eval_steps="$EVAL_STEPS" \
  --max_eval_samples=256 \
  --save_freq="$SAVE_FREQ" \
  --log_freq="$LOG_FREQ" \
  --seed="$SEED" \
  --output_dir="$OUTPUT_DIR" \
  --job_name=act_sim_cube_optimized_20260723 \
  --wandb.enable=false \
  --policy.push_to_hub=false
