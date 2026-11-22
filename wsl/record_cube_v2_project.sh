#!/usr/bin/env bash
set -euo pipefail

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

export FOLLOWER_PORT="${FOLLOWER_PORT:-/dev/ttyACM0}"
export LEADER_PORT="${LEADER_PORT:-/dev/ttyACM1}"
export FOLLOWER_ID="${FOLLOWER_ID:-R12260101}"
: "${LEADER_ID:?Set LEADER_ID to the calibrated SO101 leader id.}"

export CAMERA_SERVER="${CAMERA_SERVER:-172.28.48.1}"
export CAMERA_PORT="${CAMERA_PORT:-5555}"
export FPS="${FPS:-30}"
export EPISODE_TIME_S="${EPISODE_TIME_S:-20}"
export RESET_TIME_S="${RESET_TIME_S:-10}"
export NUM_EPISODES="${NUM_EPISODES:-20}"
export MAX_RELATIVE_TARGET="${MAX_RELATIVE_TARGET:-3.0}"
export DATASET_NAME="${DATASET_NAME:-so101_grasp_cube_v2_$(date +%Y%m%d_%H%M%S)}"
export DATASET_ROOT="${DATASET_ROOT:-$HOME/lerobot_data/$DATASET_NAME}"
export DATASET_REPO_ID="${DATASET_REPO_ID:-local/$DATASET_NAME}"
export SINGLE_TASK="${SINGLE_TASK:-Grasp the cube and lift it.}"

echo "dataset_name=$DATASET_NAME"
echo "dataset_root=$DATASET_ROOT"
echo "dataset_repo_id=$DATASET_REPO_ID"
echo "follower=$FOLLOWER_ID@$FOLLOWER_PORT"
echo "leader=$LEADER_ID@$LEADER_PORT"
echo "camera_server=$CAMERA_SERVER:$CAMERA_PORT"
echo "episodes=$NUM_EPISODES episode_time_s=$EPISODE_TIME_S reset_time_s=$RESET_TIME_S fps=$FPS"

lerobot-record \
  --robot.type=so101_follower \
  --robot.port="$FOLLOWER_PORT" \
  --robot.id="$FOLLOWER_ID" \
  --robot.disable_torque_on_disconnect=true \
  --robot.max_relative_target="$MAX_RELATIVE_TARGET" \
  --robot.cameras="{wrist: {type: zmq, server_address: '$CAMERA_SERVER', port: $CAMERA_PORT, camera_name: wrist, width: 640, height: 480, fps: $FPS, timeout_ms: 5000, warmup_s: 1}, scene: {type: zmq, server_address: '$CAMERA_SERVER', port: $CAMERA_PORT, camera_name: scene, width: 640, height: 480, fps: $FPS, timeout_ms: 5000, warmup_s: 1}}" \
  --teleop.type=so101_leader \
  --teleop.port="$LEADER_PORT" \
  --teleop.id="$LEADER_ID" \
  --dataset.repo_id="$DATASET_REPO_ID" \
  --dataset.root="$DATASET_ROOT" \
  --dataset.fps="$FPS" \
  --dataset.num_episodes="$NUM_EPISODES" \
  --dataset.episode_time_s="$EPISODE_TIME_S" \
  --dataset.reset_time_s="$RESET_TIME_S" \
  --dataset.single_task="$SINGLE_TASK" \
  --dataset.push_to_hub=false \
  --dataset.streaming_encoding=true \
  --dataset.encoder_threads=2 \
  --dataset.video_encoding_batch_size=1 \
  --dataset.tags='["so101","cube","v2","teleop"]' \
  --display_data=false \
  --play_sounds=false

