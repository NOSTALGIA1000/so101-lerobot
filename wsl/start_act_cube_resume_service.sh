#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$HOME/lerobot_outputs"
systemctl --user reset-failed act-cube-v1-resume.service >/dev/null 2>&1 || true

systemd-run --user \
  --unit=act-cube-v1-resume \
  --description=ACT_Cube_V1_Resume \
  /usr/bin/bash -lc 'exec /home/nostalgia/lerobot_ops/resume_act_cube_training.sh > /home/nostalgia/lerobot_outputs/act_cube_v1.resume_20260722.log 2>&1'

systemctl --user status act-cube-v1-resume --no-pager
