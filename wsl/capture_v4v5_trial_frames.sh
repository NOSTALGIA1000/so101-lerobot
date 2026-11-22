#!/usr/bin/env bash
set -euo pipefail

# Save scene and wrist frames for a rollout trial.
# Usage: capture_v4v5_trial_frames.sh v4|v5 STEP TRIAL before|after

MODEL="${1:?usage: capture_v4v5_trial_frames.sh v4|v5 STEP TRIAL before|after}"
STEP="${2:?step required}"
TRIAL="${3:?trial required}"
WHEN="${4:?before|after required}"

case "$MODEL" in
  v4|v5) ;;
  *) echo "unknown model: $MODEL" >&2; exit 2 ;;
esac

case "$WHEN" in
  before|after) ;;
  *) echo "unknown capture phase: $WHEN (expected before|after)" >&2; exit 2 ;;
esac

OUT_DIR="$HOME/lerobot_outputs/rollouts/frames"
mkdir -p "$OUT_DIR"

if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
  conda activate lerobot
fi

python3 /mnt/c/Users/ASUS/Documents/lerobot/wsl/capture_scene_frame.py \
  --camera scene \
  --out "$OUT_DIR/${MODEL}_${STEP}_t${TRIAL}_${WHEN}_scene.png"

python3 /mnt/c/Users/ASUS/Documents/lerobot/wsl/capture_scene_frame.py \
  --camera wrist \
  --out "$OUT_DIR/${MODEL}_${STEP}_t${TRIAL}_${WHEN}_wrist.png"
