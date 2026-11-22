#!/usr/bin/env bash
set -euo pipefail

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

export PATH="/usr/lib/wsl/lib:$PATH"

policy_path="${1:?Usage: rollout_act_cube_safe.sh /path/to/pretrained_model [camera_server_address] [max_relative_target] [duration_s]}"
camera_server="${2:-$(ip route show default | awk '{print $3; exit}')}"
max_relative_target="${3:-1.5}"
duration_s="${4:-15}"
follower_port="${FOLLOWER_PORT:-/dev/ttyACM0}"

exec lerobot-rollout \
  --strategy.type=base \
  --policy.path="$policy_path" \
  --device=cuda \
  --fps=30 \
  --robot.type=so101_follower \
  --robot.port="$follower_port" \
  --robot.id=R12260101 \
  --robot.max_relative_target="$max_relative_target" \
  --robot.cameras="{wrist: {type: zmq, server_address: $camera_server, port: 5555, camera_name: wrist, width: 640, height: 480, fps: 30}, scene: {type: zmq, server_address: $camera_server, port: 5555, camera_name: scene, width: 640, height: 480, fps: 30}}" \
  --task="Grasp the cube and lift it." \
  --duration="$duration_s" \
  --display_data=false
