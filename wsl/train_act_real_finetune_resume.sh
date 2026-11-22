#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# ACT Fine-Tune Resume: Continue from fine-tuned checkpoint
# ============================================================
# Uses fine-tuned weights as init (not sim checkpoint).
# Fresh optimizer state, same dataset.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/project_config.sh"

source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

# ---- Paths ----
RESUME_CKPT="${RESUME_CKPT:-}"  # REQUIRED: set via env or first arg
if [[ -z "$RESUME_CKPT" && $# -ge 1 ]]; then
    RESUME_CKPT="$1"
fi
if [[ -z "$RESUME_CKPT" ]]; then
    echo "ERROR: RESUME_CKPT not set. Usage:" >&2
    echo "  RESUME_CKPT=/path/to/checkpoint bash $0" >&2
    echo "  bash $0 /path/to/checkpoint" >&2
    exit 1
fi

OUTPUT_DIR="${OUTPUT_DIR:-$OUTPUT_ROOT/act_real_finetune_resume_$(date +%Y%m%d)}"
JOB_NAME="${JOB_NAME:-act_real_finetune_resume}"

STEPS="${STEPS:-10000}"
SEED="${SEED:-20260723}"

echo "============================================================"
echo "ACT Fine-Tune RESUME"
echo "============================================================"
echo "  init from:   $RESUME_CKPT"
echo "  dataset:     $REAL_REPO_ID"
echo "  dataset root:$REAL_DATASET_ROOT"
echo "  output:      $OUTPUT_DIR"
echo "  steps:       $STEPS"
echo "  batch_size:  $BATCH_SIZE"
echo "  lr:          1e-5"
echo "  eval_steps:  $EVAL_STEPS"
echo "  save_freq:   $SAVE_FREQ"
echo "============================================================"

if [[ ! -d "$RESUME_CKPT" ]]; then
    echo "ERROR: Checkpoint not found: $RESUME_CKPT" >&2
    exit 1
fi

cd "$PROJECT_ROOT"

exec nice -n 10 lerobot-train \
  --policy.path="$RESUME_CKPT" \
  --dataset.repo_id="$REAL_REPO_ID" \
  --dataset.root="$REAL_DATASET_ROOT" \
  --dataset.eval_split=0.15 \
  --optimizer.lr=1e-5 \
  --batch_size="$BATCH_SIZE" \
  --num_workers=2 \
  --prefetch_factor=2 \
  --persistent_workers=false \
  --steps="$STEPS" \
  --eval_steps="$EVAL_STEPS" \
  --max_eval_samples=256 \
  --save_freq="$SAVE_FREQ" \
  --log_freq=50 \
  --seed="$SEED" \
  --output_dir="$OUTPUT_DIR" \
  --job_name="$JOB_NAME" \
  --wandb.enable=false
