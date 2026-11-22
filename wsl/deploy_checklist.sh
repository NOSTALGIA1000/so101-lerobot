#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# Deployment Checklist — run BEFORE connecting robot
# ============================================================
# Usage: bash wsl/deploy_checklist.sh
# Prints pass/fail for each item. Non-zero exit if any check fails.
# ============================================================

PASS=0
FAIL=0

check() {
    local label="$1"
    local result="$2"
    local fix="${3:-}"
    if [[ "$result" == "OK" ]]; then
        echo "  [PASS] $label"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] $label — ${fix:-fix required}"
        FAIL=$((FAIL + 1))
    fi
}

echo "============================================================"
echo "SO-101 Cube Grasp — Deployment Checklist"
echo "============================================================"
echo ""

# 1. USB / Robot
echo "=== 1. USB & Robot Connection ==="
if [[ -e /dev/ttyACM0 ]]; then
    check "Follower serial at /dev/ttyACM0" "OK"
elif [[ -e /dev/ttyACM1 ]]; then
    check "Follower serial at /dev/ttyACM1" "OK" "(export FOLLOWER_PORT=/dev/ttyACM1)"
else
    check "Follower serial at /dev/ttyACM0" "FAIL" "Check USB cable, run: usbipd wsl list"
fi

# 2. Camera
echo ""
echo "=== 2. Camera ==="
ping -n 1 -w 2 172.28.48.1 >/dev/null 2>&1 && \
    check "Camera server reachable (172.28.48.1)" "OK" || \
    check "Camera server reachable (172.28.48.1)" "FAIL" "Check camera server is running, verify IP"

# 3. Checkpoint
echo ""
echo "=== 3. Policy Checkpoint ==="
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/project_config.sh" 2>/dev/null || true
DEPLOY_CKPT="${DEPLOY_CKPT:-$OUTPUT_ROOT/deploy_ckpt}"
if [[ -d "$DEPLOY_CKPT" && -f "$DEPLOY_CKPT/model.safetensors" ]]; then
    check "Deploy checkpoint at $DEPLOY_CKPT" "OK"
elif [[ -f "$SIM_CKPT_DIR/model.safetensors" ]]; then
    check "Deploy checkpoint at $DEPLOY_CKPT" "FAIL" "Run: ln -s $SIM_CKPT_DIR $DEPLOY_CKPT"
else
    check "Deploy checkpoint exists" "FAIL" "No checkpoint found. Run fine-tune first."
fi

# 4. Dataset verification
echo ""
echo "=== 4. Dataset ==="
DS_PATH="${REAL_DATASET_ROOT:-$HOME/lerobot_data/so101_real_cube_pick_img64}"
if [[ -f "$DS_PATH/meta/info.json" ]]; then
    check "Real dataset at $DS_PATH" "OK"
else
    check "Real dataset at $DS_PATH" "FAIL" "Run create_real_dataset_64x64.py"
fi

# 5. Safety config
echo ""
echo "=== 5. Safety ==="
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -f "$SCRIPT_DIR/safety_bounds.json" ]]; then
    check "Safety bounds config exists" "OK"
else
    check "Safety bounds config exists" "FAIL" "Create wsl/safety_bounds.json"
fi

echo ""
echo "============================================================"
echo "SUMMARY: $PASS passed, $FAIL failed"
echo "============================================================"

if [[ $FAIL -gt 0 ]]; then
    echo "Fix failures above before connecting robot."
    exit 1
else
    echo "All checks passed. Ready to connect robot."
    echo ""
    echo "Next steps:"
    echo "  1. Connect USB, verify /dev/ttyACM0 appears"
    echo "  2. Start camera server on 172.28.48.1:5555"
    echo "  3. Home robot: bash wsl/home_robot.sh"
    echo "  4. No-cube test: bash wsl/rollout_act_real_nocube.sh"
    echo "  5. Cube test:    bash wsl/rollout_act_real_cube.sh"
fi
