#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="${LOG_FILE:-/mnt/c/Users/ASUS/Documents/lerobot/wsl/act_sim_cube_until_2130.log}"
OUTPUT_DIR="${OUTPUT_DIR:-/home/nostalgia/lerobot_outputs/act_sim_cube_until_2130}"
STEPS="${STEPS:-20000}"
BATCH_SIZE="${BATCH_SIZE:-2}"
NUM_WORKERS="${NUM_WORKERS:-2}"

mkdir -p "$(dirname "$LOG_FILE")"

cat > /tmp/run_act_sim_until_2130.sh <<EOF
#!/usr/bin/env bash
set -euo pipefail
source "\$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot
export STEPS="$STEPS"
export BATCH_SIZE="$BATCH_SIZE"
export NUM_WORKERS="$NUM_WORKERS"
export OUTPUT_DIR="$OUTPUT_DIR"
exec bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/train_act_sim_smoke.sh
EOF
chmod +x /tmp/run_act_sim_until_2130.sh

nohup /tmp/run_act_sim_until_2130.sh > "$LOG_FILE" 2>&1 < /dev/null &
pid=$!
echo "training_started pid=$pid log=$LOG_FILE output_dir=$OUTPUT_DIR steps=$STEPS"
