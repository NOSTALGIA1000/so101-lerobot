# SO-ARM101 Cube Pick Project Index

Date: 2026-07-23

## Workspace Root

```text
C:\Users\ASUS\Documents\lerobot
```

## Main Project Areas

```text
simulation/
  MuJoCo SO-ARM101 cube-pick environment, synthetic dataset generation, ACT conversion notes.

training/
  BC, visual chunked BC, ACT smoke status, model status notes.

evaluation/
  Simulation evaluation scripts and outputs.

deployment/
  Sim2real safety gate and dry-run artifacts.

wsl/
  WSL-side training, dataset conversion, rollout, camera, follower, and sim2real adapter scripts.

papers/
  ACT reading guide and source paper.

camera_bridge_frames/
  Latest saved real wrist/scene camera frames.

F-CCproject/codex-project/
  Codex-maintained project memory, workflow, status, and next-step docs.
```

## Important Files

```text
REAL_DEMO_ALIGNMENT_PLAN_20260722.md
WSL_RECOVERY_STATUS_20260722.md
MEMORY_ACT_CUBE_V1_EVAL_20260722.md
simulation/ACT_LEROBOT_CONVERSION_PLAN.md
training/ACT_SMOKE_STATUS.md
deployment/REAL_ROBOT_TEST_GATE.md
wsl/convert_act_smoke_npz_to_lerobot_v3.py
wsl/train_act_sim_optimized.sh
wsl/probe_act_sim_on_real_obs.py
wsl/run_act_sim2real_adapter_micrograsp.py
```

## Current Simulation Dataset

```text
WSL path: /home/nostalgia/lerobot_data/so101_sim_cube_pick_img64
repo_id: local/so101_sim_cube_pick_img64
episodes: 20
frames: 8400
cameras: wrist, scene
image size: 64x64 in dataset metadata
state dim: 6
action dim: 6
```

## Current ACT Simulation Checkpoints

```text
/home/nostalgia/lerobot_outputs/act_sim_cube_smoke_500/checkpoints/000500/pretrained_model
/home/nostalgia/lerobot_outputs/act_sim_cube_until_2130/checkpoints/004000/pretrained_model
```

The 4000-step checkpoint is the best available sim ACT checkpoint from 2026-07-22.

## Current Real-Robot Scripts

```text
wsl/check_follower_readonly.py
wsl/check_camera_bridge.py
wsl/save_camera_bridge_frames.py
wsl/rollout_act_sim_cube_safe.sh
wsl/run_act_sim_004000_nocube_safe.sh
wsl/run_act_sim_004000_cube_micrograsp.sh
wsl/probe_act_sim_on_real_obs.py
wsl/run_act_sim2real_adapter_micrograsp.py
```

## Current Limitation

The sim ACT policy uses MuJoCo-style state/action semantics, while the real SO-ARM101 follower exposes joint state/action in degrees plus a follower-specific gripper scale. Direct deployment therefore requires an adapter and still does not solve the visual domain gap.
