#!/usr/bin/env bash
set -euo pipefail

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot
export PATH="/usr/lib/wsl/lib:$PATH"

policy_path="${1:?Usage: eval_act_cube_10_trials.sh /path/to/pretrained_model [evaluation_name] [camera_server]}"
evaluation_name="${2:-eval_act_cube_v1}"
camera_server="${3:-$(ip route show default | awk '{print $3; exit}')}"
follower_port="${FOLLOWER_PORT:-/dev/ttyACM0}"
evaluation_root="$HOME/lerobot_evaluations/$evaluation_name"

if [[ -e "$evaluation_root" ]]; then
  echo "Refusing to overwrite existing evaluation: $evaluation_root" >&2
  echo "Choose another evaluation_name or explicitly resume it." >&2
  exit 1
fi

exec lerobot-rollout \
  --strategy.type=episodic \
  --strategy.reset_to_initial_position=true \
  --policy.path="$policy_path" \
  --device=cuda \
  --fps=30 \
  --robot.type=so101_follower \
  --robot.port="$follower_port" \
  --robot.id=R12260101 \
  --robot.max_relative_target=3.0 \
  --robot.cameras="{wrist: {type: zmq, server_address: $camera_server, port: 5555, camera_name: wrist, width: 640, height: 480, fps: 30}, scene: {type: zmq, server_address: $camera_server, port: 5555, camera_name: scene, width: 640, height: 480, fps: 30}}" \
  --task="Grasp the cube and lift it." \
  --dataset.repo_id="local/$evaluation_name" \
  --dataset.root="$evaluation_root" \
  --dataset.single_task="Grasp the cube and lift it." \
  --dataset.fps=30 \
  --dataset.episode_time_s=20 \
  --dataset.reset_time_s=30 \
  --dataset.num_episodes=10 \
  --dataset.tags='["so101","act","cube","evaluation"]' \
  --dataset.push_to_hub=false \
  --display_data=false
