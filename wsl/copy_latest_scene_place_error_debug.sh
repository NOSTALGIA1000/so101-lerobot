#!/usr/bin/env bash
set -euo pipefail

debug_dir="/home/nostalgia/lerobot_outputs/rollouts/scene_place_error_debug_20260730"
latest="$(find "$debug_dir" -name '*place_error.jpg' -type f | sort | tail -n 1)"
cp "$latest" /mnt/c/Users/ASUS/Documents/lerobot/scene_place_error_latest.jpg
echo "/mnt/c/Users/ASUS/Documents/lerobot/scene_place_error_latest.jpg"
