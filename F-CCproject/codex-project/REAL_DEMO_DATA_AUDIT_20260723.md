# Real Demo Data Audit

Date: 2026-07-23

## Summary

Real demonstration data **already exists** in LeRobot v3.0 format. No conversion from raw format needed.

## Data Location

```
C:\Users\ASUS\Documents\lerobot\datasets\so101_grasp_cube_test_20260721_200217\
WSL path: /mnt/c/Users/ASUS/Documents/lerobot/datasets/so101_grasp_cube_test_20260721_200217/
```

## Dataset Inventory

| Item | Path | Size |
|------|------|------|
| info.json | meta/info.json | ~2 KB |
| stats.json | meta/stats.json | ~8 KB |
| tasks.parquet | meta/tasks.parquet | ~1 KB |
| episodes (chunk 0) | meta/episodes/chunk-000/file-000.parquet | 67 KB |
| episodes (chunk 1) | meta/episodes/chunk-000/file-001.parquet | 187 KB |
| data (chunk 0) | data/chunk-000/file-000.parquet | 249 KB |
| data (chunk 1) | data/chunk-000/file-001.parquet | 620 KB |
| scene video (0) | videos/observation.images.scene/chunk-000/file-000.mp4 | 65 MB |
| scene video (1) | videos/observation.images.scene/chunk-000/file-001.mp4 | 121 MB |
| wrist video (0) | videos/observation.images.wrist/chunk-000/file-000.mp4 | 51 MB |
| wrist video (1) | videos/observation.images.wrist/chunk-000/file-001.mp4 | 88 MB |

**Total:** ~326 MB

## Dataset Schema

### Metadata (info.json)

```json
{
  "codebase_version": "v3.0",
  "fps": 30,
  "robot_type": "so_follower",       // ← REAL robot, NOT sim ("so101")
  "total_episodes": 46,
  "total_frames": 19958,
  "total_tasks": 1,
  "splits": {"train": "0:46"}
}
```

### Features

| Feature | dtype | shape | Description |
|---------|-------|-------|-------------|
| action | float32 | [6] | Target joint positions (degrees, follower scale) |
| observation.state | float32 | [6] | Current joint positions (degrees, follower scale) |
| observation.images.wrist | video | [480, 640, 3] | Wrist-mounted camera, AV1, 30fps |
| observation.images.scene | video | [480, 640, 3] | Scene camera, AV1, 30fps |
| timestamp | float32 | [1] | Episode-relative time in seconds |
| frame_index | int64 | [1] | Episode-relative frame index |
| episode_index | int64 | [1] | Global episode index [0, 45] |
| index | int64 | [1] | Global frame index [0, 19957] |
| task_index | int64 | [1] | Task index (always 0, single task) |

### Joint Names (action + observation.state, same order)

```
0: shoulder_pan.pos
1: shoulder_lift.pos
2: elbow_flex.pos
3: wrist_flex.pos
4: wrist_roll.pos
5: gripper.pos
```

## State/Action Semantics: REAL SO Follower (DEGREES)

This is the critical finding. The dataset uses **real SO-ARM101 follower units**, NOT MuJoCo simulation units.

### Observation.State Statistics

| Joint | Min | Max | Mean | Std | Unit |
|-------|-----|-----|------|-----|------|
| shoulder_pan.pos | -79.12 | 34.02 | -9.41 | 12.64 | degrees |
| shoulder_lift.pos | -103.96 | 71.08 | -51.66 | 57.17 | degrees |
| elbow_flex.pos | -93.76 | 96.48 | 40.50 | 54.37 | degrees |
| wrist_flex.pos | 13.54 | 102.15 | 73.40 | 17.83 | degrees |
| wrist_roll.pos | -17.41 | 56.53 | 4.12 | 7.54 | degrees |
| gripper.pos | 2.56 | 67.31 | 21.94 | 17.55 | follower units |

### Action Statistics

| Joint | Min | Max | Mean | Std | Unit |
|-------|-----|-----|------|-----|------|
| shoulder_pan.pos | -79.65 | 34.46 | -9.34 | 12.68 | degrees |
| shoulder_lift.pos | -104.79 | 70.95 | -52.17 | 56.89 | degrees |
| elbow_flex.pos | -96.66 | 96.57 | 39.57 | 54.47 | degrees |
| wrist_flex.pos | 12.62 | 102.20 | 73.19 | 18.11 | degrees |
| wrist_roll.pos | -18.55 | 57.85 | 4.05 | 7.60 | degrees |
| gripper.pos | 0.08 | 67.85 | 15.42 | 19.57 | follower units |

### Sim Dataset Comparison (for reference)

Sim dataset `local/so101_sim_cube_pick_img64` uses:
- **Units:** radians (joint positions in rad, gripper in normalized [0,1] or rad-equivalent)
- **Scale:** shoulder_lift ~[-1.26, 0.10] vs real ~[-104, 71]
- **Ratio:** real_degrees ≈ sim_radians × (180/π) ≈ sim_radians × 57.3

### Verification: Real vs Sim Scale

From `REAL_DEMO_ALIGNMENT_PLAN_20260722.md`:
- Real `shoulder_lift.pos` ≈ -95.5 (degrees)
- Sim training range for same dim ≈ [-1.26, 0.10] (radians)
- -95.5° / -1.67 rad ≈ 57.2 ≈ 180/π ✓

**Conclusion:** State/action semantics confirmed as real SO follower degrees. This matches deployment semantics exactly.

## Image Statistics

### Scene Camera
- Resolution: 640×480
- Channels: 3 (RGB, normalized [0,1])
- Mean: [0.696, 0.686, 0.709] (RGB)
- Std: [0.297, 0.300, 0.283]

### Wrist Camera
- Resolution: 640×480
- Channels: 3 (RGB, normalized [0,1])
- Mean: [0.605, 0.483, 0.392] (RGB)
- Std: [0.159, 0.156, 0.189]

Wrist camera has lower variance and more blue-ish cast (lower red channel mean) — consistent with close-up wrist-mounted view of table/robot workspace.

## Episode Structure

- Total: 46 episodes
- Total frames: 19,958
- Average frames/episode: 19958/46 ≈ 434 frames ≈ 14.5 seconds
- Max frame_index: 856 → longest episode ~28.5 seconds
- FPS: 30
- Recording script: `record_so101_zmq.sh` with `--dataset.episode_time_s=30`

## Data Completeness Assessment

| Check | Status | Detail |
|-------|--------|--------|
| info.json valid | PASS | v3.0, all required fields |
| stats.json valid | PASS | All features have stats |
| Parquet data readable | PASS (verified by validate_cube_dataset.py) | |
| Videos playable | NOT VERIFIED | Need WSL-side video decode check |
| State/action aligned | PASS | Same 6-DoF joint order |
| Timestamps monotonic | PASS | 0.0 to 28.53s, per-episode |
| Episode boundaries consistent | PASS | 46 episodes, frames sum to 19958 |
| No missing frames | PASS | Frame indices sequential within episodes |
| Robot calibration present | PASS | R12260101.json exists |
| Task labels | PASS | Single task: "Grasp the cube and lift it" |

## Gaps Identified

1. **No train/eval split.** All 46 episodes in "train" split. Need to reserve ~5-10 episodes for validation.
2. **No success/failure labels per episode.** All episodes treated equally. Unknown which episodes actually achieved cube grasp.
3. **Video codec is AV1.** May cause decode performance issues. Sim dataset used H.264. Need to verify AV1 decode works in training loop.
4. **No dataset version tag.** Single timestamped recording session. If we record more demos, need versioning strategy.
5. **Gripper action range anomaly.** Action min is 0.08 but state min is 2.56. The action has a lower floor (more closed). This is expected (teleoperator commands full close) but worth noting.

## Next Actions

1. ✅ Data location confirmed
2. ✅ Schema analyzed
3. 🔜 Verify video decoding in WSL training env
4. 🔜 Create train/eval split
5. 🔜 Design fine-tune config
6. 🔜 Write fine-tune script
