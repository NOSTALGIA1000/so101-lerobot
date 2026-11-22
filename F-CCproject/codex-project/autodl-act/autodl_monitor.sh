#!/bin/bash
set -euo pipefail

echo "=== time ==="
date

echo "=== gpu ==="
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null || true

echo "=== python training processes ==="
ps -eo pid,etime,pcpu,pmem,cmd | grep -E 'lerobot_train|lerobot.scripts.lerobot_train' | grep -v grep || true

echo "=== output dirs ==="
find /root/autodl-tmp/lerobot_outputs -maxdepth 3 -type d 2>/dev/null | sort || true

echo "=== recent checkpoints ==="
find /root/autodl-tmp/lerobot_outputs -path '*/checkpoints/*/pretrained_model' -type d 2>/dev/null | sort || true

echo "=== recent logs ==="
for f in /root/autodl-tmp/lerobot_outputs/*train.log /root/autodl-tmp/*.nohup.log /root/autodl-tmp/so101_merge_v3v6.log; do
  [ -f "$f" ] || continue
  echo "--- $f ---"
  tail -40 "$f"
done

