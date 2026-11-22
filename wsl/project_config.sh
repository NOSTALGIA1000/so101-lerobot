#!/usr/bin/env bash
# ============================================================
# project_config.sh — Single source of truth for all paths
# ============================================================
# Source this in every script:  source "$(dirname "$0")/project_config.sh"
# Override any variable via env before sourcing.
# ============================================================

# ---- Workspace ----
if [ -d "$HOME/lerobot_workspace/lerobot" ]; then
    PROJECT_ROOT="$HOME/lerobot_workspace/lerobot"
else
    PROJECT_ROOT="/mnt/c/Users/ASUS/Documents/lerobot"
fi

# ---- Conda ----
CONDA_BASE="$HOME/miniconda3"
CONDA_ENV="lerobot"

# ---- Datasets ----
REAL_DATASET_ROOT="${REAL_DATASET_ROOT:-$HOME/lerobot_data/so101_real_cube_pick_img64}"
REAL_REPO_ID="${REAL_REPO_ID:-local/so101_real_cube_pick_img64}"

SIM_DATASET_ROOT="${SIM_DATASET_ROOT:-$HOME/lerobot_data/so101_sim_cube_pick_img64_100ep}"
SIM_REPO_ID="${SIM_REPO_ID:-local/so101_sim_cube_pick_img64_100ep}"

# ---- Checkpoints ----
SIM_CKPT_DIR="${SIM_CKPT_DIR:-$HOME/lerobot_outputs/act_sim_100ep_20260723_v2/checkpoints/018000/pretrained_model}"
DEPLOY_CKPT="${DEPLOY_CKPT:-$HOME/lerobot_outputs/deploy_ckpt}"

# ---- Output root ----
OUTPUT_ROOT="${OUTPUT_ROOT:-$HOME/lerobot_outputs}"

# ---- Training defaults (8GB VRAM safe) ----
BATCH_SIZE="${BATCH_SIZE:-2}"
LR_FINETUNE="${LR_FINETUNE:-1e-5}"
STEPS_FINETUNE="${STEPS_FINETUNE:-10000}"
EVAL_STEPS="${EVAL_STEPS:-500}"
SAVE_FREQ="${SAVE_FREQ:-1000}"

# ---- Hardware / Robot ----
FOLLOWER_PORT="${FOLLOWER_PORT:-/dev/ttyACM0}"
CAMERA_SERVER="${CAMERA_SERVER:-172.28.48.1}"
ROBOT_ID="${ROBOT_ID:-R12260101}"

# ---- Misc ----
export PATH="/usr/lib/wsl/lib:$PATH"
export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-2}"
