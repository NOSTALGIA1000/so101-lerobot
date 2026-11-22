# Real → LeRobot Fine-Tune Plan

Date: 2026-07-23

## Status: Data Already in LeRobot v3 Format

The real demonstration dataset at `datasets/so101_grasp_cube_test_20260721_200217/` is **already in LeRobot v3.0 format**. No raw→LeRobot conversion step needed.

The work reduces to:
1. Preprocessing (resolution adaptation for sim checkpoint compatibility)
2. Train/eval split
3. Fine-tune config design
4. Training script
5. Evaluation on hardware

## Key Design Decision: Image Resolution

### Problem

| Dataset | Image Size | State/Action Unit |
|---------|-----------|-------------------|
| Sim (`so101_sim_cube_pick_img64`) | 64×64 | radians |
| Real (`so101_grasp_cube_test_20260721_200217`) | 640×480 | degrees |

The sim ACT checkpoint at 4000 steps was trained on 64×64 images. Fine-tuning from this checkpoint requires architecture compatibility.

### Decision: Create 64×64 Real Dataset Variant

**Approach:** Downsample real videos to 64×64, create a new LeRobot dataset at that resolution, fine-tune from sim checkpoint.

**Rationale:**
- Guarantees architecture compatibility with sim checkpoint
- 64×64 is sufficient for cube grasp (sim policy achieved reasonable behavior at this resolution)
- Fine-tuning adapts visual features from sim→real domain even at low resolution
- Faster training iteration (smaller images = less GPU memory, faster data loading)
- If results are promising, can later increase resolution

**Alternative considered:** Train from scratch at 640×480. Rejected for first iteration — can't leverage sim pretraining, much slower training.

## Step-by-Step Plan

### Step 1: Create 64×64 Real Dataset

Script: `wsl/create_real_dataset_64x64.py`

Operations:
1. Load original 640×480 real dataset via LeRobotDataset
2. Resize each frame's wrist + scene images to 64×64 (cv2.resize or torch interpolate)
3. Write new LeRobot v3 dataset with 64×64 videos (H.264)
4. Compute and write stats.json
5. Write info.json with proper metadata

Output path: `/home/nostalgia/lerobot_data/so101_real_cube_pick_img64`
Repo ID: `local/so101_real_cube_pick_img64`

### Step 2: Create Train/Eval Split

Current dataset has all 46 episodes in "train" split. Need validation split.

Split: `train=0:40, eval=40:46` (40 train, 6 eval)

This is done in the dataset creation script by setting the `splits` field in info.json.

### Step 3: Verify Dataset

Checks:
- `LeRobotDataset` can load the new dataset
- All 46 episodes present
- Image shape is [64, 64, 3]
- State/action shapes are [6]
- Stats computed correctly
- Videos play back without corruption

### Step 4: Design Fine-Tune Config

```bash
Policy: ACT
Vision backbone: resnet18 (same as sim)
Batch size: 2 (same as sim, GPU memory constraint)
Learning rate: 1e-5 (lower than default 1e-4 for fine-tuning)
Steps: 5000-10000 (smaller dataset, fine-tuning needs fewer steps)
Eval frequency: 500 steps
Save frequency: 1000 steps
Dataset: local/so101_real_cube_pick_img64
Pretrained checkpoint: /home/nostalgia/lerobot_outputs/act_sim_cube_until_2130/checkpoints/004000/pretrained_model
```

### Step 5: Fine-Tune Script

Script: `wsl/train_act_real_finetune.sh`

Key differences from sim training:
- `--dataset.repo_id=local/so101_real_cube_pick_img64`
- `--pretrained_path` or manual checkpoint loading
- Lower learning rate
- Fewer total steps (fine-tuning converges faster)
- Eval on held-out real episodes

### Step 6: Evaluate on Hardware

After fine-tuning produces checkpoint:
1. `probe_act_real_on_real_obs.py` — dry-run inference, no action sent
2. `rollout_act_real_nocube.sh` — reach/grip test without cube
3. `rollout_act_real_cube.sh` — cube contact test
4. Only then: grasp/lift attempt

## Normalization Handling

LeRobot training normalizes data per-feature using dataset stats.json. When fine-tuning:
- Real dataset stats are used for normalization
- The normalization transform converts real degrees → ~N(0,1) internally
- Pretrained weights expect ~N(0,1) inputs (from sim normalization)
- Therefore: normalization layer automatically bridges the unit gap
- The model just needs to adapt to the different distribution SHAPE (real joint coupling vs sim)

No manual unit conversion needed. The LeRobot framework handles this.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| AV1 decode slow in training | Medium | Medium | Transcode to H.264 during 64×64 conversion |
| 46 episodes insufficient | Medium | High | Plan to record more demos if fine-tune loss plateaus high |
| Sim checkpoint incompatible | Low | High | Can fall back to train-from-scratch on real data |
| Fine-tune overfits small dataset | Medium | Medium | Use eval split, monitor eval loss, early stopping |
| CUDA OOM with 640×480 | N/A | N/A | Using 64×64 avoids this entirely |

## Files to Create

| File | Purpose |
|------|---------|
| `wsl/create_real_dataset_64x64.py` | Downsample real dataset to 64×64 |
| `wsl/train_act_real_finetune.sh` | Fine-tune ACT on real 64×64 data |
| `wsl/probe_act_real_on_real_obs.py` | Dry-run inference with real-data checkpoint |
| `wsl/rollout_act_real_nocube.sh` | Safe no-cube reach/grip test |
| `wsl/rollout_act_real_cube.sh` | Cube contact test |

## Dependencies

- WSL `lerobot` conda env with LeRobot package
- CUDA available in WSL
- Python packages: `torch`, `pyarrow`, `av`, `opencv-python`, `lerobot`
- ~2 GB free disk for 64×64 dataset (~326 MB → ~30 MB for 64×64 videos)
