#!/usr/bin/env python3
"""Downsample real SO-101 dataset 640x480 -> 64x64 for ACT fine-tune.

Input:  local/so101_grasp_cube_test_20260721_200217  (640x480, AV1, 46 eps)
Output: local/so101_real_cube_pick_img64              (64x64, H.264, 46 eps)

Uses LeRobotDataset.create() + streaming encoding for efficient write.
Sets train/eval split at episode 40 (40 train, 6 eval).
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import cv2
import numpy as np
from lerobot.datasets.lerobot_dataset import LeRobotDataset

SRC_REPO = "local/so101_grasp_cube_test_20260721_200217"
SRC_ROOT = Path.home() / "lerobot_data" / "so101_grasp_cube_test_20260721_200217"
DST_REPO = "local/so101_real_cube_pick_img64"
DST_ROOT = Path.home() / "lerobot_data" / "so101_real_cube_pick_img64"
TARGET_H, TARGET_W = 64, 64
TRAIN_EPISODES = 40
EVAL_EPISODES = 6
FPS = 30
TASK_TEXT = "Grasp the cube and lift it."
ROBOT_TYPE = "so_follower"


def features_spec() -> dict:
    return {
        "action": {
            "dtype": "float32",
            "shape": [6],
            "names": [
                "shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos",
                "wrist_flex.pos", "wrist_roll.pos", "gripper.pos",
            ],
        },
        "observation.state": {
            "dtype": "float32",
            "shape": [6],
            "names": [
                "shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos",
                "wrist_flex.pos", "wrist_roll.pos", "gripper.pos",
            ],
        },
        "observation.images.wrist": {
            "dtype": "video",
            "shape": [TARGET_H, TARGET_W, 3],
            "names": ["height", "width", "channels"],
        },
        "observation.images.scene": {
            "dtype": "video",
            "shape": [TARGET_H, TARGET_W, 3],
            "names": ["height", "width", "channels"],
        },
    }


def resize_frame(tensor, target_size):
    """Resize a single image tensor from LeRobot format (C,H,W, float32 [0,1])
    to a uint8 (H,W,C) numpy array at the target resolution.
    """
    arr = tensor.numpy()
    if arr.shape[0] == 3:
        arr = arr.transpose(1, 2, 0)
    if arr.dtype == np.float32 and arr.max() <= 1.01:
        arr = (arr * 255).astype(np.uint8)
    elif arr.dtype != np.uint8:
        arr = arr.astype(np.uint8)
    return cv2.resize(arr, target_size, interpolation=cv2.INTER_AREA)


def main() -> None:
    if DST_ROOT.exists():
        print(f"Removing existing {DST_ROOT}")
        shutil.rmtree(DST_ROOT)

    print(f"Loading source dataset: {SRC_REPO}  root={SRC_ROOT}")
    t0 = time.time()
    src = LeRobotDataset(SRC_REPO, root=SRC_ROOT)
    print(f"  episodes={src.num_episodes}  frames={len(src)}  load_time={time.time()-t0:.1f}s")

    src_meta = src.meta
    orig_shape = src_meta.features["observation.images.scene"]["shape"]
    print(f"  source image shape: {orig_shape}")

    print(f"Creating output dataset: {DST_REPO}  root={DST_ROOT}")
    dst = LeRobotDataset.create(
        repo_id=DST_REPO,
        root=DST_ROOT,
        fps=FPS,
        features=features_spec(),
        robot_type=ROBOT_TYPE,
        use_videos=True,
        streaming_encoding=True,
        encoder_threads=2,
    )

    total_written = 0
    for ep_idx in range(src.num_episodes):
        ep_info = src.meta.episodes[ep_idx]
        ep_from = int(ep_info["dataset_from_index"])
        ep_to = int(ep_info["dataset_to_index"])
        n_frames = ep_to - ep_from

        print(f"  episode {ep_idx:02d}: {n_frames:4d} frames  [{ep_from}:{ep_to}]", end="", flush=True)

        for frame_idx in range(ep_from, ep_to):
            frame = src[frame_idx]

            wrist_64 = resize_frame(frame["observation.images.wrist"], (TARGET_W, TARGET_H))
            scene_64 = resize_frame(frame["observation.images.scene"], (TARGET_W, TARGET_H))

            new_frame = {
                "action": frame["action"].numpy().astype(np.float32),
                "observation.state": frame["observation.state"].numpy().astype(np.float32),
                "observation.images.wrist": wrist_64,
                "observation.images.scene": scene_64,
                "task": TASK_TEXT,
            }
            dst.add_frame(new_frame)

        dst.save_episode()
        total_written += n_frames
        print(f"  saved")

    print(f"Finalizing dataset...")
    dst.finalize()
    print(f"  total frames written: {total_written}")

    info_path = DST_ROOT / "meta" / "info.json"
    info = json.loads(info_path.read_text())
    info["splits"] = {
        "train": f"0:{TRAIN_EPISODES}",
        "eval": f"{TRAIN_EPISODES}:{TRAIN_EPISODES + EVAL_EPISODES}",
    }
    info["robot_type"] = ROBOT_TYPE
    info_path.write_text(json.dumps(info, indent=4), encoding="utf-8")

    elapsed = time.time() - t0
    print(f"\nDone  elapsed={elapsed:.0f}s  fps={total_written/elapsed:.1f}")
    print(f"  output: {DST_ROOT}")
    print(f"  repo_id: {DST_REPO}")
    print(f"  splits:  train=0:{TRAIN_EPISODES}  eval={TRAIN_EPISODES}:{TRAIN_EPISODES+EVAL_EPISODES}")


if __name__ == "__main__":
    main()
