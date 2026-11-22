# Model Status

Date: 2026-07-22

## Current Simulation Model

The model trained in the current MuJoCo simulation pipeline is **BC**, not ACT.

More specifically:

```text
model family: Behavior Cloning
variant: chunked BC
implementation: NumPy MLP
checkpoint: training/outputs/chunk_bc_bootstrap_20_c10.npz
input: observation.state + cube_position + phase
output: 10-step action chunk
action_dim: 6
```

This is an ACT-style baseline only in the sense that it predicts action chunks.
It is not a transformer and it does not use image observations.

## Current Result

```text
evaluation: evaluation/outputs/chunk_bc_bootstrap_20_c10_eval.json
episodes: 20
success_rate: 0.60
mean_max_cube_height_m: 0.0830
```

## What ACT Means Here

Full ACT for this project should be:

```text
RGB image(s) + robot state -> action chunk
```

Expected inputs:

- wrist camera RGB
- scene camera RGB
- robot joint state

Expected output:

- SO-101 6D action chunk

## Existing ACT Real-Robot Path

There is an older ACT v1 real-robot path in `wsl/`:

```text
wsl/rollout_act_cube_safe.sh
wsl/run_safe_rollout_logged.sh
```

That path uses a LeRobot ACT checkpoint, historically:

```text
/home/nostalgia/lerobot_outputs/act_cube_v1/checkpoints/050000/pretrained_model
```

This is separate from the current MuJoCo chunked BC checkpoint. The current
NumPy BC checkpoint cannot be passed directly to `lerobot-rollout`.

## Deployment Boundary

Current MuJoCo BC policy is:

```text
deployment_status: dry_run_only
real_robot_go_no_go: no_cube_grasp_yet
```

Allowed next step:

- restore WSL
- run follower read-only check
- run no-cube low-speed safety checks

Not recommended yet:

- autonomous cube grasp with the MuJoCo BC policy
- treating the NumPy BC checkpoint as a LeRobot ACT checkpoint

## Visual Smoke Baseline

An image-observation smoke path has also been added:

```text
dataset: simulation/outputs/act_smoke_dataset_20img64
checkpoint: training/outputs/visual_chunk_bc_20img64_c10_p16_h512_s1000.npz
evaluation: evaluation/outputs/visual_chunk_bc_20img64_c10_p16_h512_s1000_eval.json
success_rate: 0.30 on 10 episodes
```

This is still BC, not ACT. It uses fixed average-pooled RGB features and a NumPy
MLP. Its purpose is to validate:

```text
RGB scene + RGB wrist + robot state -> action chunk
```

before moving to a real ACT transformer checkpoint.
