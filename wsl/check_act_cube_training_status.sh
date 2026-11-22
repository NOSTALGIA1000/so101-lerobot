#!/usr/bin/env bash
set -euo pipefail

unit="act-cube-v1-resume.service"
log="$HOME/lerobot_outputs/act_cube_v1.resume_20260722.log"
ckpt_dir="$HOME/lerobot_outputs/act_cube_v1/checkpoints"

echo "UNIT_STATUS=$(systemctl --user is-active "$unit" 2>/dev/null || true)"
echo "UNIT_DETAIL="
systemctl --user status "$unit" --no-pager 2>/dev/null | sed -n '1,18p' || true

echo "TRAIN_PROCESSES="
ps -eo pid,etime,pcpu,pmem,args | grep -E 'lerobot-train|resume_act_cube_training' | grep -v grep || true

echo "CHECKPOINTS="
if [ -d "$ckpt_dir" ]; then
  find "$ckpt_dir" -maxdepth 1 -mindepth 1 -type d -printf '%f\n' | sort
  if [ -L "$ckpt_dir/last" ]; then
    echo "last -> $(readlink "$ckpt_dir/last")"
  fi
fi

echo "LOG_TAIL="
if [ -f "$log" ]; then
  echo "log_size=$(stat -c '%s' "$log")"
  tail -n 120 "$log" | grep -aE 'step:|Resum|resume|checkpoint|INFO|ERROR|Traceback|RuntimeError|CUDA' | tail -n 40 || true
else
  echo "NO_LOG_YET"
fi
