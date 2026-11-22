#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# Fine-Tuning Experiment Grid Launcher
# ============================================================
# Runs 6 FT experiments in 3 batches (2 concurrent each).
# 8GB VRAM limit: 2 concurrent x batch_size=2 = 4 total.
#
# Grid:
#   FT-1: baseline     LR=1e-5  (sim init)
#   FT-2: low_lr       LR=5e-6  (sim init)
#   FT-3: freeze_bb    LR=1e-5  (lr_backbone=0)
#   FT-4: peft         LR=1e-5  (use_peft=true)
#   FT-5: high_lr      LR=2e-5  (sim init)
#   FT-6: from_scratch LR=1e-4  (no sim init)
#
# Usage: bash wsl/launch_ft_grid.sh [--dry-run]
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/project_config.sh"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "DRY RUN MODE — printing commands only"
fi

TODAY="$(date +%Y%m%d)"
LOGDIR="$OUTPUT_ROOT/ft_experiments_$TODAY"
mkdir -p "$LOGDIR"

run_exp() {
    local exp=$1
    shift
    local logfile="$LOGDIR/${exp}.log"
    local cmd="EXP=$exp TODAY=$TODAY STEPS=10000 BATCH_SIZE=2 EVAL_STEPS=500 SAVE_FREQ=1000 EXTRA_ARGS=\"$*\" bash $SCRIPT_DIR/run_ft_experiment.sh"

    echo "  [$exp] $cmd"
    echo "  [$exp] log: $logfile"

    if $DRY_RUN; then
        return 0
    fi

    # Run in background, redirect to log
    (
        source "$CONDA_BASE/etc/profile.d/conda.sh"
        conda activate "$CONDA_ENV"
        cd "$PROJECT_ROOT"
        EXP="$exp" TODAY="$TODAY" STEPS=10000 BATCH_SIZE=2 \
            EVAL_STEPS=500 SAVE_FREQ=1000 \
            EXTRA_ARGS="$*" \
            bash "$SCRIPT_DIR/run_ft_experiment.sh"
    ) > "$logfile" 2>&1 &
    local pid=$!
    echo "  [$exp] PID=$pid"
    echo "$pid" > "$LOGDIR/${exp}.pid"
    return 0
}

wait_all() {
    echo ""
    echo "Waiting for batch to complete..."
    local failed=0
    local pids=("$@")
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            echo "  PID $pid FAILED"
            failed=1
        else
            echo "  PID $pid done"
        fi
    done
    return $failed
}

echo "============================================================"
echo "FT Experiment Grid: 6 experiments, 3 batches"
echo "============================================================"
echo "  log dir:  $LOGDIR"
echo "  sim ckpt: $SIM_CKPT_DIR"
echo "  dataset:  $REAL_DATASET_ROOT"
echo ""

# ── Batch 1: FT-1 + FT-2 ────────────────────────────────
echo "=== BATCH 1/3: FT-1 (baseline) + FT-2 (low_lr) ==="
run_exp "FT-1" "--policy.path=$SIM_CKPT_DIR --optimizer.lr=1e-5"
pid1=$(cat "$LOGDIR/FT-1.pid" 2>/dev/null || echo 0)
run_exp "FT-2" "--policy.path=$SIM_CKPT_DIR --optimizer.lr=5e-6"
pid2=$(cat "$LOGDIR/FT-2.pid" 2>/dev/null || echo 0)
if ! $DRY_RUN; then wait_all "$pid1" "$pid2"; fi
echo ""

# ── Batch 2: FT-3 + FT-4 ────────────────────────────────
echo "=== BATCH 2/3: FT-3 (freeze_bb) + FT-4 (peft) ==="
run_exp "FT-3" "--policy.path=$SIM_CKPT_DIR --optimizer.lr=1e-5 --policy.optimizer_lr_backbone=0"
pid1=$(cat "$LOGDIR/FT-3.pid" 2>/dev/null || echo 0)
run_exp "FT-4" "--policy.path=$SIM_CKPT_DIR --optimizer.lr=1e-5 --policy.use_peft=true"
pid2=$(cat "$LOGDIR/FT-4.pid" 2>/dev/null || echo 0)
if ! $DRY_RUN; then wait_all "$pid1" "$pid2"; fi
echo ""

# ── Batch 3: FT-5 + FT-6 ────────────────────────────────
echo "=== BATCH 3/3: FT-5 (high_lr) + FT-6 (from_scratch) ==="
run_exp "FT-5" "--policy.path=$SIM_CKPT_DIR --optimizer.lr=2e-5"
pid1=$(cat "$LOGDIR/FT-5.pid" 2>/dev/null || echo 0)
run_exp "FT-6" "--optimizer.lr=1e-4"
pid2=$(cat "$LOGDIR/FT-6.pid" 2>/dev/null || echo 0)
if ! $DRY_RUN; then wait_all "$pid1" "$pid2"; fi

echo ""
echo "============================================================"
echo "All 6 experiments complete."
echo "Logs: $LOGDIR/"
echo "============================================================"
echo ""
echo "Next: evaluate with python wsl/eval_checkpoints.py"
