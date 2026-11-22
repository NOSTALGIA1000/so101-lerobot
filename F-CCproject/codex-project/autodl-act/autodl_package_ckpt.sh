#!/bin/bash
set -euo pipefail

RUN_NAME="${1:-}"
case "$RUN_NAME" in
  v2)
    OUT=/root/autodl-tmp/lerobot_outputs/act_cube_place_v2
    ;;
  v3v6)
    OUT=/root/autodl-tmp/lerobot_outputs/act_cube_white_paper_v3v6
    ;;
  v4)
    OUT=/root/autodl-tmp/lerobot_outputs/act_bottle_place_v4
    ;;
  v5)
    OUT=/root/autodl-tmp/lerobot_outputs/act_cap_on_cube_v5
    ;;
  *)
    echo "Usage: bash autodl_package_ckpt.sh {v2|v3v6|v4|v5}"
    exit 2
    ;;
esac

mkdir -p /root/autodl-tmp/so101_ckpt_packages
LATEST=$(find "$OUT/checkpoints" -maxdepth 2 -type d -name pretrained_model 2>/dev/null | sort | tail -1)
if [ -z "$LATEST" ]; then
  echo "No pretrained_model checkpoint found under $OUT/checkpoints"
  exit 1
fi

CKPT_DIR=$(dirname "$LATEST")
PKG=/root/autodl-tmp/so101_ckpt_packages/${RUN_NAME}_$(basename "$CKPT_DIR")_pretrained_model.tar.gz
tar -C "$CKPT_DIR" -czf "$PKG" pretrained_model
echo "$PKG"
