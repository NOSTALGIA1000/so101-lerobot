#!/usr/bin/env bash
set -euo pipefail

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

LOG_DIR="$HOME/lerobot_outputs/rollouts"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/v2_050000_cube_10s_gripper_bias10_thr35.log"

POLICY="/mnt/f/CC-project/lerobot-storage/outputs/real_test_candidates/act_v2_050000/checkpoints/050000/pretrained_model"

export ROLLOUT_TASK="Small real-robot cube contact test. Approach the visible cube slowly, align the gripper, gently close on the cube. Do not lift or place."
export ROLLOUT_GRIPPER_CLOSE_BIAS=10
export ROLLOUT_GRIPPER_CLOSE_THRESHOLD=35

timeout --signal=INT 60s \
  lerobot-rollout \
    --strategy.type=base \
    --policy.path="$POLICY" \
    --device=cuda \
    --fps=30 \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=R12260101 \
    --robot.cameras="{wrist: {type: zmq, server_address: 172.28.48.1, port: 5555, camera_name: wrist, width: 64, height: 64, fps: 30}, scene: {type: zmq, server_address: 172.28.48.1, port: 5555, camera_name: scene, width: 64, height: 64, fps: 30}}" \
    --rename_map='{"observation.images.scene": "observation.images.overhead"}' \
    --task="$ROLLOUT_TASK" \
    --duration=10 \
    --display_data=false \
    >"$LOG_FILE" 2>&1

status=$?
echo "exit_status=$status"
echo "log=$LOG_FILE"
grep -aE 'Policy loaded|Robot connected|ZMQCamera|Rollout setup complete|control loop started|running slower|Duration limit reached|Rollout finished|disconnected|ERROR|Traceback|RuntimeError|EOFError' "$LOG_FILE" | tail -120 || true
echo "---LOG_TAIL---"
tail -80 "$LOG_FILE"
exit "$status"
