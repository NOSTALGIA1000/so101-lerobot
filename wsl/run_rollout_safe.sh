#!/usr/bin/env bash
# Wrapper to run rollout scripts with clean WSL bash (avoid Git Bash in PATH)
set -euo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$HOME/miniconda3/envs/lerobot/bin:$HOME/miniconda3/condabin"
exec /usr/bin/bash "$@"
