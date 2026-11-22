#!/usr/bin/env bash
set -euo pipefail

source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lerobot

LOG_DIR="$HOME/lerobot_outputs/rollouts"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/v2_050000_cube_10s_actionlog.log"
ACTION_LOG="$LOG_DIR/v2_050000_cube_10s_actionlog.csv"
rm -f "$ACTION_LOG"

POLICY="/mnt/f/CC-project/lerobot-storage/outputs/real_test_candidates/act_v2_050000/checkpoints/050000/pretrained_model"

export ROLLOUT_TASK="Small real-robot cube contact test. Approach the visible cube slowly, align the gripper, gently close on the cube. Do not lift or place."
unset ROLLOUT_GRIPPER_CLOSE_BIAS
unset ROLLOUT_GRIPPER_CLOSE_THRESHOLD
export ROLLOUT_ACTION_LOG_PATH="$ACTION_LOG"
export ROLLOUT_DEBUG_ACTION=1

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
echo "action_log=$ACTION_LOG"
grep -aE 'Policy loaded|Robot connected|ZMQCamera|Rollout setup complete|control loop started|running slower|Duration limit reached|Rollout finished|disconnected|ERROR|Traceback|RuntimeError|EOFError' "$LOG_FILE" | tail -120 || true
echo "---ACTION_LOG_HEAD---"
head -5 "$ACTION_LOG" 2>/dev/null || true
echo "---ACTION_LOG_TAIL---"
tail -20 "$ACTION_LOG" 2>/dev/null || true
exit "$status"
