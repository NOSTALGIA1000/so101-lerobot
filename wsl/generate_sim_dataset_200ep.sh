#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# Generate large MuJoCo dataset (200 eps, 64x64) and convert to LeRobot v3
# Uses parallel multiprocessing for NPZ generation.
# ============================================================
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot
export PATH="/usr/lib/wsl/lib:$PATH"
export MUJOCO_GL=egl

EPISODES="${1:-200}"
IMAGE_SIZE="${2:-64}"
SEED="${3:-42}"
WORKERS="${4:-5}"
SIM_WORK="$HOME/sim_work"
NPZ_OUT="$HOME/sim_dataset_npz_${EPISODES}ep"
LEROBOT_OUT="$HOME/lerobot_data/so101_sim_cube_pick_img64_v2"

echo "============================================================"
echo "Phase 1: Parallel NPZ Generation"
echo "============================================================"
echo "  episodes:  $EPISODES"
echo "  img_size:  $IMAGE_SIZE"
echo "  workers:   $WORKERS"
echo "  seed:      $SEED"
echo "  output:    $NPZ_OUT"

cd "$SIM_WORK"

if [ -d "$NPZ_OUT" ]; then
    echo "Removing existing $NPZ_OUT"
    rm -rf "$NPZ_OUT"
fi

START=$(date +%s)
python /mnt/c/tmp/generate_parallel.py \
    --episodes "$EPISODES" \
    --image-size "$IMAGE_SIZE" \
    --seed "$SEED" \
    --output-dir "$NPZ_OUT" \
    --workers "$WORKERS"

ELAPSED=$(( $(date +%s) - START ))
FPS=$(python -c "import json; m=json.load(open('$NPZ_OUT/meta/info.json')); print(f\"{m['total_frames']/$ELAPSED:.1f}\")")
echo "Generated in ${ELAPSED}s ($FPS fps)"

echo ""
echo "============================================================"
echo "Phase 2: Export manifest"
echo "============================================================"
python simulation/dataset_generation/export_act_manifest.py \
    --dataset-dir "$NPZ_OUT" \
    --output "$NPZ_OUT/manifest.json"

echo ""
echo "============================================================"
echo "Phase 3: Convert to LeRobot v3"
echo "============================================================"
echo "  output: $LEROBOT_OUT"

if [ -d "$LEROBOT_OUT" ]; then
    echo "Removing existing $LEROBOT_OUT"
    rm -rf "$LEROBOT_OUT"
fi

cd /mnt/c/Users/ASUS/Documents/lerobot
python wsl/convert_act_smoke_npz_to_lerobot_v3.py \
    --dataset-dir "$NPZ_OUT" \
    --output-root "$LEROBOT_OUT" \
    --overwrite

echo ""
echo "============================================================"
echo "Phase 4: Validate"
echo "============================================================"
python -c "
from lerobot.datasets.lerobot_dataset import LeRobotDataset
d = LeRobotDataset('local/so101_sim_cube_pick_img64_v2', root='$LEROBOT_OUT')
print(f'  episodes: {d.num_episodes}')
print(f'  frames:   {len(d)}')
print(f'  features: {list(d.features.keys())}')
print(f'  stats:    OK')
"

echo "DONE"
echo "  dataset: $LEROBOT_OUT"
echo "  repo_id: local/so101_sim_cube_pick_img64_v2"
