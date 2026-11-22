#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# ACT Training on 200-episode Sim Dataset (64x64)
# ============================================================
# Trains ACT from scratch on large MuJoCo sim dataset.
# Dataset: local/so101_sim_cube_pick_img64_v2 (200 eps, ~84K frames)
# Model: ACT + resnet18 (~52M params), AMP enabled for RTX 4060.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/project_config.sh"

source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

DATASET_ROOT="${DATASET_ROOT:-$SIM_DATASET_ROOT}"
REPO_ID="${REPO_ID:-$SIM_REPO_ID}"
OUTPUT_DIR="${OUTPUT_DIR:-$OUTPUT_ROOT/act_sim_200ep_$(date +%Y%m%d)}"
JOB_NAME="${JOB_NAME:-act_sim_200ep}"

STEPS="${STEPS:-20000}"
BATCH_SIZE="${BATCH_SIZE:-4}"
NUM_WORKERS="${NUM_WORKERS:-2}"
EVAL_STEPS="${EVAL_STEPS:-1000}"
SAVE_FREQ="${SAVE_FREQ:-2000}"
LOG_FREQ="${LOG_FREQ:-50}"
SEED="${SEED:-20260723}"

echo "============================================================"
echo "ACT Training: 200-episode Sim Dataset"
echo "============================================================"
echo "  dataset:     $REPO_ID"
echo "  root:        $DATASET_ROOT"
echo "  output:      $OUTPUT_DIR"
echo "  steps:       $STEPS"
echo "  batch_size:  $BATCH_SIZE"
echo "  save_freq:   $SAVE_FREQ"
echo "  eval_steps:  $EVAL_STEPS"
echo "============================================================"

if [[ ! -d "$DATASET_ROOT" ]]; then
    echo "ERROR: Dataset not found: $DATASET_ROOT" >&2
    echo "Generate first: bash wsl/generate_sim_dataset_200ep.sh" >&2
    exit 1
fi

if [ -d "$PROJECT_ROOT" ]; then
    cd "$PROJECT_ROOT"
else
    cd /mnt/c/Users/ASUS/Documents/lerobot
fi

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
  --job_name="$JOB_NAME" \
  --wandb.enable=false \
  --policy.push_to_hub=false
