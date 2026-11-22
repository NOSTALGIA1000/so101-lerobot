#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# ACT Fine-Tune: Sim Checkpoint -> Real 64x64 Dataset
# ============================================================
# Uses --policy.path to load pretrained sim ACT weights while
# computing normalization stats from the real dataset.
# Learning rate lowered 10x vs from-scratch training.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/project_config.sh"

source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

# ---- Paths ----
OUTPUT_DIR="${OUTPUT_DIR:-$OUTPUT_ROOT/act_real_finetune_sim018K_lr1e-5_$(date +%Y%m%d)}"
JOB_NAME="${JOB_NAME:-act_real_finetune_sim018K}"

# ---- Validate inputs ----
if [[ ! -d "$SIM_CKPT_DIR" ]]; then
    echo "ERROR: Sim checkpoint not found: $SIM_CKPT_DIR" >&2
    echo "Expected: config.json + model.safetensors inside" >&2
    exit 1
fi

if [[ ! -f "$SIM_CKPT_DIR/config.json" ]]; then
    echo "ERROR: config.json missing in $SIM_CKPT_DIR" >&2
    exit 1
fi

if [[ ! -f "$SIM_CKPT_DIR/model.safetensors" ]]; then
    echo "ERROR: model.safetensors missing in $SIM_CKPT_DIR" >&2
    exit 1
fi

if [[ ! -d "$REAL_DATASET_ROOT" ]]; then
    echo "ERROR: Real 64x64 dataset not found: $REAL_DATASET_ROOT" >&2
    echo "Run create_real_dataset_64x64.py first." >&2
    exit 1
fi

echo "============================================================"
echo "ACT Fine-Tune: Real-Data Adaptation"
echo "============================================================"
echo "  pretrained:  $SIM_CKPT_DIR"
echo "  dataset:     $REAL_REPO_ID"
echo "  dataset root:$REAL_DATASET_ROOT"
echo "  output:      $OUTPUT_DIR"
echo "  steps:       $STEPS_FINETUNE"
echo "  batch_size:  $BATCH_SIZE"
echo "  lr:          $LR_FINETUNE"
echo "  eval_steps:  $EVAL_STEPS"
echo "  save_freq:   $SAVE_FREQ"
echo "============================================================"

cd "$PROJECT_ROOT"

exec nice -n 10 lerobot-train \
  --policy.path="$SIM_CKPT_DIR" \
  --dataset.repo_id="$REAL_REPO_ID" \
  --dataset.root="$REAL_DATASET_ROOT" \
  --dataset.eval_split=0.15 \
  --optimizer.lr="$LR_FINETUNE" \
  --batch_size="$BATCH_SIZE" \
  --num_workers=2 \
  --prefetch_factor=2 \
  --persistent_workers=false \
  --steps="$STEPS_FINETUNE" \
  --eval_steps="$EVAL_STEPS" \
  --max_eval_samples=256 \
  --save_freq="$SAVE_FREQ" \
  --log_freq=50 \
  --seed="${SEED:-20260723}" \
  --output_dir="$OUTPUT_DIR" \
  --job_name="$JOB_NAME" \
  --wandb.enable=false
