# Step 5: Expert Dataset Generation

Date: 2026-07-22

## Status

Implemented the first expert demonstration generator and validated small-batch
dataset generation after the Windows restart.

## Files Added

- `simulation/dataset_generation/generate_expert_dataset.py`
- `simulation/dataset_generation/__init__.py`

## Method

The current expert is a MuJoCo Jacobian IK controller with scripted task phases:

1. Move above cube.
2. Descend to pre-grasp.
3. Close gripper.
4. Lift.
5. Move to place region.
6. Lower.
7. Open gripper.

## Output Format

The first dataset format is lightweight and dependency-minimal:

- `meta/info.json`
- `episodes/episode_000000.npz`

Each episode contains:

- `observation.state`
- `observation.velocity`
- `action`
- `cube_position`
- `cube_orientation`
- `reward`
- `success`
- `timestamp`
- `frame_index`
- `episode_index`

This is not yet full LeRobot v3 parquet/video format. It is a smoke-test format for expert logic and action/state alignment.

## Next Work

- Keep the current `abstract_grasp` path as a bootstrap simulator primitive.
- Tune gripper/contact so pure physical grasp success is reliable.
- Add image capture sampling or video writing.
- Convert the lightweight dataset into LeRobot parquet/video layout.
- Generate larger batches after success metrics are stable.

## 2026-07-22 Runtime Check

Generated datasets:

- `simulation/outputs/expert_dataset_env_grasp_smoke_1`
  - episodes: 1
  - frames: 420
  - action/state shape: 6
- `simulation/outputs/expert_dataset_env_grasp_5`
  - episodes: 5
  - frames: 2100
  - lift success in any frame: 60%
- `simulation/outputs/expert_dataset_bootstrap_5`
  - episodes: 5
  - frames: 2100
  - lift success in any frame: 100%
- `simulation/outputs/expert_dataset_bootstrap_20`
  - episodes: 20
  - frames: 8400
  - lift success in any frame: 100%

The current SO-101 asset exposes 5 arm joints plus 1 gripper joint, so the
action/state dimension is 6. We should not fabricate a seventh joint unless a
different SO-ARM101 model asset is introduced.
