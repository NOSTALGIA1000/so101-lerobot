#!/usr/bin/env bash
set -euo pipefail

# Prepare/check the compact MuJoCo ACT-smoke dataset from Windows.
# This script does not start training. It verifies that WSL can see the compact
# NPZ manifest and reports the remaining conversion step to LeRobot v3.

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

DATASET_DIR="${DATASET_DIR:-/mnt/c/Users/ASUS/Documents/lerobot/simulation/outputs/act_smoke_dataset_20img64}"
MANIFEST="$DATASET_DIR/manifest.json"
export MANIFEST

if [[ ! -f "$MANIFEST" ]]; then
  echo "missing_manifest=$MANIFEST" >&2
  echo "Run from Windows first:" >&2
  echo "python simulation/dataset_generation/export_act_manifest.py --dataset-dir simulation/outputs/act_smoke_dataset_20img64 --output simulation/outputs/act_smoke_dataset_20img64/manifest.json" >&2
  exit 2
fi

python - <<'PY'
import json
import os
from pathlib import Path

manifest = Path(os.environ["MANIFEST"])
data = json.loads(manifest.read_text())
required = {
    "format",
    "total_episodes",
    "total_frames",
    "camera_keys",
    "image_shape",
    "features",
    "episodes",
}
missing = sorted(required - set(data))
if missing:
    raise SystemExit(f"manifest_missing_keys={missing}")
print(f"manifest={manifest}")
print(f"format={data['format']}")
print(f"episodes={data['total_episodes']}")
print(f"frames={data['total_frames']}")
print(f"image_shape={data['image_shape']}")
print(f"camera_keys={data['camera_keys']}")
print("compact_npz_manifest=PASS")
PY

echo
echo "next_required_step=convert compact NPZ to LeRobot v3 parquet/video or add a LeRobot-compatible adapter dataset"
echo "training_note=current lerobot-train ACT scripts expect LeRobotDataset, not compact NPZ"
