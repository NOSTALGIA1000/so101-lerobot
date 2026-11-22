# ACT LeRobot Conversion Plan

Date: 2026-07-22

## Current Input Dataset

Compact NPZ image dataset:

```text
simulation/outputs/act_smoke_dataset_20img64
```

Manifest:

```text
simulation/outputs/act_smoke_dataset_20img64/manifest.json
```

Current content:

```text
episodes: 20
frames: 8400
fps: 30
cameras: observation.images.scene, observation.images.wrist
image shape: 64 x 64 x 3
state/action shape: 6
```

## Target Format

LeRobot v3 dataset layout, matching the real SO-101 dataset:

```text
data/chunk-000/file-000.parquet
meta/info.json
meta/stats.json
meta/tasks.parquet
meta/episodes/chunk-000/file-000.parquet
videos/observation.images.scene/chunk-000/file-000.mp4
videos/observation.images.wrist/chunk-000/file-000.mp4
```

Reference real dataset:

```text
datasets/so101_grasp_cube_test_20260721_200217
```

## Feature Mapping

| Compact NPZ key | LeRobot v3 key | dtype | shape |
|---|---|---:|---:|
| `action` | `action` | float32 | `[6]` |
| `observation.state` | `observation.state` | float32 | `[6]` |
| `observation.images.scene` | `observation.images.scene` | video | `[64,64,3]` |
| `observation.images.wrist` | `observation.images.wrist` | video | `[64,64,3]` |
| `timestamp` | `timestamp` | float32 | `[1]` |
| `frame_index` | `frame_index` | int64 | `[1]` |
| `episode_index` | `episode_index` | int64 | `[1]` |
| constant `0` | `task_index` | int64 | `[1]` |
| global frame id | `index` | int64 | `[1]` |

## Required Dependencies

The current Windows sandbox intentionally avoided heavy dependency installs.
Conversion should run in WSL/LeRobot after WSL is healthy:

- `pyarrow`
- `pandas` or `polars`
- `pyav` or LeRobot's video writer stack
- `lerobot`

## Execution Plan

1. Restore WSL distro. **Done.**
2. Run:

   ```bash
   bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/prepare_sim_act_smoke.sh
   ```

3. Convert compact NPZ to LeRobot v3 dataset. **Done.**
4. Validate using `LeRobotDataset`. **Done.**
5. Run ACT smoke training. **Done for 500 steps.**

   ```bash
   lerobot-train \
     --dataset.repo_id=local/so101_sim_cube_pick_img64 \
     --dataset.root=$HOME/lerobot_data/so101_sim_cube_pick_img64 \
     --policy.type=act \
     --policy.device=cuda \
     --batch_size=2 \
     --steps=2000 \
     --output_dir=$HOME/lerobot_outputs/act_sim_cube_smoke \
     --wandb.enable=false
   ```

## Important Boundary

The current visual smoke checkpoint:

```text
training/outputs/visual_chunk_bc_20img64_c10_p16_h512_s1000.npz
```

is not ACT and cannot be passed to `lerobot-rollout`.

## Current Converted Dataset

```text
root: /home/nostalgia/lerobot_data/so101_sim_cube_pick_img64
repo_id: local/so101_sim_cube_pick_img64
episodes: 20
frames: 8400
video files: 40
LeRobotDataset validation: PASS
```

## Current ACT Checkpoint

```text
checkpoint: /home/nostalgia/lerobot_outputs/act_sim_cube_smoke_500/checkpoints/000500/pretrained_model
steps: 500
eval_loss: 0.4129
```
