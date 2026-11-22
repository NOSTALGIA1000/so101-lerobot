#!/usr/bin/env bash
set -euo pipefail

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

LOG_DIR="$HOME/lerobot_outputs/rollouts"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/v7_cube_10s_mrt003.log"

POLICY="/mnt/f/CC-project/lerobot-storage/outputs/real_test_candidates/act_v7_050000/pretrained_model/checkpoints/050000/pretrained_model"

export ROLLOUT_TASK="Small real-robot cube contact test. Approach the visible cube slowly, align the gripper, gently close on the cube. Do not lift or place."

timeout --signal=INT 70s \
  lerobot-rollout \
    --strategy.type=base \
    --policy.path="$POLICY" \
    --device=cuda \
    --fps=30 \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=R12260101 \
    --robot.max_relative_target=0.03 \
    --robot.cameras="{wrist: {type: zmq, server_address: 172.28.48.1, port: 5555, camera_name: wrist, width: 64, height: 64, fps: 30}, scene: {type: zmq, server_address: 172.28.48.1, port: 5555, camera_name: scene, width: 64, height: 64, fps: 30}}" \
    --rename_map='{"observation.images.scene": "observation.images.overhead"}' \
    --task="$ROLLOUT_TASK" \
    --duration=10 \
    --display_data=false \
    >"$LOG_FILE" 2>&1

status=$?
echo "exit_status=$status"
grep -aE 'Policy loaded|Robot connected|ZMQCamera|Rollout setup complete|control loop started|running slower|clamped|Duration limit reached|Rollout finished|disconnected|ERROR|Traceback|RuntimeError|EOFError' "$LOG_FILE" | tail -100 || true
echo "---LOG_TAIL---"
tail -60 "$LOG_FILE"
exit "$status"
