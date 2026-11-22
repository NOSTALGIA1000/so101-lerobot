#!/usr/bin/env bash
set -euo pipefail

CORE="/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py"
grep -n -E "ROLLOUT_GRIPPER|ROLLOUT_ACTION_LOG|action_dict|robot_action_processor|send_action|ordered_keys" "$CORE" | head -120
