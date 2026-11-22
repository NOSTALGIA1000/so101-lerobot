# ACT Smoke Path Status

Date: 2026-07-22

## What Was Added Today

Compact image/state/action dataset generation:

```text
simulation/dataset_generation/generate_act_smoke_dataset.py
```

Visual chunked BC smoke training:

```text
training/train_visual_chunk_bc.py
```

Visual chunked BC smoke evaluation:

```text
evaluation/evaluate_visual_chunk_bc.py
```

Compact NPZ ACT sample adapter sanity check:

```text
training/act_npz_adapter_sanity.py
```

## Dataset

```text
simulation/outputs/act_smoke_dataset_20img64
episodes: 20
frames: 8400
image_size: 64x64
cameras: scene, wrist
format: compact NPZ
```

Each episode stores:

- `observation.images.scene`
- `observation.images.wrist`
- `observation.state`
- `cube_position`
- `ee_position`
- `action`
- `success`
- `timestamp`
- `frame_index`
- `episode_index`

This is not yet full LeRobot parquet/video format.

Manifest:

```text
simulation/outputs/act_smoke_dataset_20img64/manifest.json
```

Adapter sanity result:

```text
samples: 8400
scene image: 64 x 64 x 3
wrist image: 64 x 64 x 3
state: 6
action chunk: 10 x 6
status: PASS
```

## Smoke Model

```text
checkpoint: training/outputs/visual_chunk_bc_20img64_c10_p16_h512_s1000.npz
model family: visual chunked BC smoke baseline
image encoder: fixed 16x16 average pooling
policy head: NumPy MLP
input: pooled scene RGB + pooled wrist RGB + robot state + phase
output: 10-step action chunk
```

This is still not ACT. It only validates the visual observation path.

## Result

```text
evaluation: evaluation/outputs/visual_chunk_bc_20img64_c10_p16_h512_s1000_eval.json
episodes: 10
success_rate: 0.30
mean_max_cube_height_m: 0.0617
```

## Interpretation

The image-to-action-chunk path is now working. The visual smoke baseline has
closed-loop behavior, but fixed pooled image features are too weak for robust
deployment.

## Next Step Toward ACT

LeRobot ACT smoke training is now running through the real `lerobot-train`
pipeline:

```text
RGB scene + RGB wrist + robot state -> action chunk
```

## LeRobot v3 Conversion

Converter:

```text
wsl/convert_act_smoke_npz_to_lerobot_v3.py
```

Converted dataset:

```text
/home/nostalgia/lerobot_data/so101_sim_cube_pick_img64
repo_id: local/so101_sim_cube_pick_img64
episodes: 20
frames: 8400
videos: 40 mp4 files
LeRobotDataset validation: PASS
```

## ACT Smoke Checkpoint

Startup test:

```text
/home/nostalgia/lerobot_outputs/act_sim_cube_smoke_startup/checkpoints/000005/pretrained_model
steps: 5
status: PASS
```

First real ACT smoke checkpoint:

```text
/home/nostalgia/lerobot_outputs/act_sim_cube_smoke_500/checkpoints/000500/pretrained_model
steps: 500
eval_loss: 0.4129
status: PASS
```

Training command:

```text
wsl/train_act_sim_smoke.sh
```

Current ACT model details:

```text
policy.type: act
vision_backbone: resnet18
parameters: 52M
dataset: local/so101_sim_cube_pick_img64
batch_size: 2
device: cuda
```

Remaining work:

1. Train beyond 500 steps, likely 5k-20k for a meaningful checkpoint.
2. Add simulation rollout adapter for LeRobot ACT checkpoints.
3. Evaluate ACT in simulation before any real robot rollout.
4. Only after stable sim eval, run no-cube real robot safety rollout.
