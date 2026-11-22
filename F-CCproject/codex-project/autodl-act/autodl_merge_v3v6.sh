#!/bin/bash
set -euo pipefail

export HF_HOME=/root/autodl-tmp/hf
export HF_LEROBOT_HOME=/root/autodl-tmp/lerobot
export PYTHONPATH=/root/lerobot_workspace/lerobot/src:${PYTHONPATH:-}

cd /root/lerobot_workspace/lerobot
LOG=/root/autodl-tmp/so101_merge_v3v6.log
if command -v lerobot-edit-dataset >/dev/null 2>&1; then
  EDIT_DATASET=(lerobot-edit-dataset)
else
  EDIT_DATASET=(python -m lerobot.scripts.lerobot_edit_dataset)
fi

{
  echo "=== merge V3+V6 ==="
  date
  echo "Input 1: RItcheOhe/so101_cube_place_v3"
  echo "Input 2: RItcheOhe/so101_cube_white_paper_v6"
  echo "Output : RItcheOhe/so101_cube_white_paper_v3v6"

  "${EDIT_DATASET[@]}" \
    --repo_id RItcheOhe/so101_cube_white_paper_v3v6 \
    --operation.type merge \
    --operation.repo_ids "['RItcheOhe/so101_cube_place_v3', 'RItcheOhe/so101_cube_white_paper_v6']" \
    --push_to_hub true

  echo "=== info merged ==="
  "${EDIT_DATASET[@]}" \
    --repo_id RItcheOhe/so101_cube_white_paper_v3v6 \
    --operation.type info || true
} 2>&1 | tee "$LOG"
