#!/usr/bin/env bash
set -euo pipefail

output_dir=/home/nostalgia/lerobot_outputs/act_cube_v1
log_file=/home/nostalgia/lerobot_outputs/act_cube_v1.train.log

if [[ -e "$output_dir" ]]; then
  echo "Refusing to overwrite existing output: $output_dir" >&2
  exit 1
fi

mkdir -p /home/nostalgia/lerobot_outputs
systemd-run --user \
  --unit=act-cube-v1 \
  --description=ACT_Cube_V1_Training \
  /usr/bin/bash -lc "exec /home/nostalgia/lerobot_ops/train_act_cube.sh > '$log_file' 2>&1"

echo "Training unit started: act-cube-v1.service"
echo "Log: $log_file"
