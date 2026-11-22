#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# Single Fine-Tune Experiment Runner
# ============================================================
# Usage:
#   EXP=FT-1 EXTRA_ARGS="--optimizer.lr=1e-5" bash run_ft_experiment.sh
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/project_config.sh"

source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

EXP="${EXP:-FT-0}"
EXTRA_ARGS="${EXTRA_ARGS:-}"
TODAY="${TODAY:-$(date +%Y%m%d)}"
OUTPUT_DIR="${OUTPUT_DIR:-$OUTPUT_ROOT/act_real_ft_${EXP}_${TODAY}}"
JOB_NAME="act_ft_${EXP}"

STEPS="${STEPS:-10000}"
SEED="${SEED:-20260723}"

echo "============================================================"
echo "FT Experiment: $EXP"
echo "============================================================"
echo "  output:      $OUTPUT_DIR"
echo "  dataset:     $REAL_REPO_ID"
echo "  dataset root:$REAL_DATASET_ROOT"
echo "  steps:       $STEPS"
echo "  batch_size:  $BATCH_SIZE"
echo "  extra_args:  $EXTRA_ARGS"
echo "============================================================"

if [[ ! -d "$REAL_DATASET_ROOT" ]]; then
    echo "ERROR: Real dataset not found: $REAL_DATASET_ROOT" >&2
    exit 1
fi

cd "$PROJECT_ROOT"

exec nice -n 10 lerobot-train \
  --dataset.repo_id="$REAL_REPO_ID" \
  --dataset.root="$REAL_DATASET_ROOT" \
  --dataset.eval_split=0.15 \
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
  --wandb.enable=false \
  $EXTRA_ARGS
