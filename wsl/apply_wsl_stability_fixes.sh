#!/usr/bin/env bash
set -euo pipefail

# Run as root inside LeRobot-Ubuntu-F:
#   sudo bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/apply_wsl_stability_fixes.sh
#
# Purpose:
# - Increase Linux shared memory (/dev/shm) for PyTorch/DataLoader workloads.
# - Keep the change persistent across WSL restarts.

SHM_SIZE="${SHM_SIZE:-6G}"
FSTAB="/etc/fstab"
BACKUP="/etc/fstab.bak_$(date +%Y%m%d_%H%M%S)"

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run as root, e.g. sudo bash $0" >&2
  exit 1
fi

mkdir -p /dev/shm

if [ -f "$FSTAB" ]; then
  cp "$FSTAB" "$BACKUP"
else
  touch "$FSTAB"
  cp "$FSTAB" "$BACKUP"
fi

python3 - "$FSTAB" "$SHM_SIZE" <<'PY'
import sys
from pathlib import Path

fstab = Path(sys.argv[1])
size = sys.argv[2]
lines = fstab.read_text().splitlines()
lines = [ln for ln in lines if "/dev/shm" not in ln.split("#", 1)[0]]
lines.append(f"tmpfs /dev/shm tmpfs defaults,size={size},mode=1777 0 0")
fstab.write_text("\n".join(lines) + "\n")
PY

mountpoint -q /dev/shm && mount -o remount /dev/shm || mount /dev/shm

echo "Configured /dev/shm size=$SHM_SIZE"
df -h /dev/shm
echo "Backup: $BACKUP"
