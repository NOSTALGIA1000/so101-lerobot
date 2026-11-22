#!/bin/bash
set -euo pipefail

LOG=/root/autodl-tmp/so101_setup_env.log
mkdir -p /root/autodl-tmp /root/so101_autodl /root/lerobot_workspace

{
  echo "=== basic ==="
  date
  hostname
  whoami
  df -h / /root/autodl-tmp || true

  echo "=== gpu ==="
  nvidia-smi || true

  echo "=== python ==="
  python -V
  python - <<'PY'
try:
    import torch
    print("torch", torch.__version__, "cuda", torch.cuda.is_available())
except Exception as exc:
    print("torch_error", repr(exc))
PY

  echo "=== install lerobot if needed ==="
  if [ ! -d /root/lerobot_workspace/lerobot/.git ]; then
    git clone https://github.com/huggingface/lerobot.git /root/lerobot_workspace/lerobot
  fi
  cd /root/lerobot_workspace/lerobot
  python -m pip install -U pip
  python -m pip install -e ".[training]"

  echo "=== lerobot check ==="
  python - <<'PY'
import lerobot
print("lerobot_import ok")
PY
  python -m lerobot.scripts.lerobot_train --help >/tmp/so101_lerobot_train_help.txt 2>&1 || true
  lerobot-edit-dataset --help >/tmp/so101_edit_help.txt 2>&1 || true

  echo "=== hf auth ==="
  hf auth whoami 2>&1 || huggingface-cli whoami 2>&1 || true

  echo "Setup complete. If HF auth failed, run: hf auth login"
} 2>&1 | tee "$LOG"

