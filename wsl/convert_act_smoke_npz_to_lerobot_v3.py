#!/usr/bin/env python3
"""Convert compact SO-101 ACT-smoke NPZ data to a LeRobot v3-style dataset.

Run inside the WSL `lerobot` conda env where pyarrow and av are available.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import av
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


ACTION_NAMES = [
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
]
TASK = "Pick the cube and lift it."


def fixed_list_array(values: np.ndarray, dim: int) -> pa.FixedSizeListArray:
    flat = pa.array(values.reshape(-1).astype(np.float32), type=pa.float32())
    return pa.FixedSizeListArray.from_arrays(flat, dim)


def write_video(path: Path, frames: np.ndarray, fps: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    container = av.open(str(path), mode="w")
    stream = container.add_stream("libx264", rate=fps)
    stream.width = int(frames.shape[2])
    stream.height = int(frames.shape[1])
    stream.pix_fmt = "yuv420p"
    stream.options = {"crf": "23", "preset": "veryfast"}
    for frame in frames:
        video_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
        for packet in stream.encode(video_frame):
            container.mux(packet)
    for packet in stream.encode():
        container.mux(packet)
    container.close()


def stats(values: np.ndarray) -> dict[str, list[float] | list[int]]:
    v = values.astype(np.float64)
    return {
        "min": v.min(axis=0).tolist(),
        "max": v.max(axis=0).tolist(),
        "mean": v.mean(axis=0).tolist(),
        "std": v.std(axis=0).tolist(),
        "count": [int(v.shape[0])] * int(v.shape[1]),
        "q01": np.quantile(v, 0.01, axis=0).tolist(),
        "q10": np.quantile(v, 0.10, axis=0).tolist(),
        "q50": np.quantile(v, 0.50, axis=0).tolist(),
        "q90": np.quantile(v, 0.90, axis=0).tolist(),
        "q99": np.quantile(v, 0.99, axis=0).tolist(),
    }


def image_stats(values: np.ndarray) -> dict[str, list[list[list[float]]] | list[int]]:
    """Return channel stats in LeRobot-compatible nested shape.

    LeRobot image stats are stored as 3 x 1 x 1 nested lists for C,H,W tensors.
    """

    v = values.astype(np.float32) / 255.0
    flat = v.reshape(-1, 3)
    return {
        "min": flat.min(axis=0)[:, None, None].tolist(),
        "max": flat.max(axis=0)[:, None, None].tolist(),
        "mean": flat.mean(axis=0)[:, None, None].tolist(),
        "std": flat.std(axis=0)[:, None, None].tolist(),
        "count": [int(v.shape[0])],
        "q01": np.quantile(flat, 0.01, axis=0)[:, None, None].tolist(),
        "q10": np.quantile(flat, 0.10, axis=0)[:, None, None].tolist(),
        "q50": np.quantile(flat, 0.50, axis=0)[:, None, None].tolist(),
        "q90": np.quantile(flat, 0.90, axis=0)[:, None, None].tolist(),
        "q99": np.quantile(flat, 0.99, axis=0)[:, None, None].tolist(),
    }


def write_main_parquet(output_root: Path, rows: dict[str, np.ndarray]) -> None:
    table = pa.table(
        {
            "action": fixed_list_array(rows["action"], 6),
            "observation.state": fixed_list_array(rows["state"], 6),
            "timestamp": pa.array(rows["timestamp"].astype(np.float32), type=pa.float32()),
            "frame_index": pa.array(rows["frame_index"].astype(np.int64), type=pa.int64()),
            "episode_index": pa.array(rows["episode_index"].astype(np.int64), type=pa.int64()),
            "index": pa.array(rows["index"].astype(np.int64), type=pa.int64()),
            "task_index": pa.array(rows["task_index"].astype(np.int64), type=pa.int64()),
        }
    )
    path = output_root / "data" / "chunk-000" / "file-000.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


def write_meta(output_root: Path, source_manifest: dict[str, object], rows: dict[str, np.ndarray], episode_rows: list[dict[str, object]], image_rows: dict[str, np.ndarray], image_shape: list[int], fps: int) -> None:
    meta = output_root / "meta"
    (meta / "episodes" / "chunk-000").mkdir(parents=True, exist_ok=True)

    info = {
        "codebase_version": "v3.0",
        "fps": fps,
        "features": {
            "action": {"dtype": "float32", "shape": [6], "names": ACTION_NAMES},
            "observation.state": {"dtype": "float32", "shape": [6], "names": ACTION_NAMES},
            "observation.images.wrist": {
                "dtype": "video",
                "shape": image_shape,
                "names": ["height", "width", "channels"],
                "info": {
                    "is_depth_map": False,
                    "video.height": image_shape[0],
                    "video.width": image_shape[1],
                    "video.codec": "h264",
                    "video.pix_fmt": "yuv420p",
                    "video.fps": fps,
                    "video.channels": 3,
                    "has_audio": False,
                    "video.g": 2,
                    "video.crf": 23,
                    "video.preset": "veryfast",
                    "video.fast_decode": 0,
                    "video.video_backend": "pyav",
                    "video.extra_options": {},
                },
            },
            "observation.images.scene": {
                "dtype": "video",
                "shape": image_shape,
                "names": ["height", "width", "channels"],
                "info": {
                    "is_depth_map": False,
                    "video.height": image_shape[0],
                    "video.width": image_shape[1],
                    "video.codec": "h264",
                    "video.pix_fmt": "yuv420p",
                    "video.fps": fps,
                    "video.channels": 3,
                    "has_audio": False,
                    "video.g": 2,
                    "video.crf": 23,
                    "video.preset": "veryfast",
                    "video.fast_decode": 0,
                    "video.video_backend": "pyav",
                    "video.extra_options": {},
                },
            },
            "timestamp": {"dtype": "float32", "shape": [1], "names": None},
            "frame_index": {"dtype": "int64", "shape": [1], "names": None},
            "episode_index": {"dtype": "int64", "shape": [1], "names": None},
            "index": {"dtype": "int64", "shape": [1], "names": None},
            "task_index": {"dtype": "int64", "shape": [1], "names": None},
        },
        "total_episodes": int(source_manifest["total_episodes"]),
        "total_frames": int(source_manifest["total_frames"]),
        "total_tasks": 1,
        "chunks_size": 1000,
        "data_files_size_in_mb": 100,
        "video_files_size_in_mb": 200,
        "data_path": "data/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet",
        "video_path": "videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4",
        "robot_type": "so101",
        "splits": {"train": f"0:{int(source_manifest['total_episodes'])}"},
    }
    (meta / "info.json").write_text(json.dumps(info, indent=4), encoding="utf-8")

    global_stats = {
        "action": stats(rows["action"]),
        "observation.state": stats(rows["state"]),
        "observation.images.scene": image_stats(image_rows["scene"]),
        "observation.images.wrist": image_stats(image_rows["wrist"]),
        "timestamp": stats(rows["timestamp"][:, None]),
        "frame_index": stats(rows["frame_index"][:, None]),
        "episode_index": stats(rows["episode_index"][:, None]),
        "index": stats(rows["index"][:, None]),
        "task_index": stats(rows["task_index"][:, None]),
    }
    (meta / "stats.json").write_text(json.dumps(global_stats, indent=4), encoding="utf-8")

    pq.write_table(pa.table({"task_index": pa.array([0], type=pa.int64()), "task": pa.array([TASK], type=pa.string())}), meta / "tasks.parquet")

    ep_cols = {key: [] for key in episode_rows[0]}
    for row in episode_rows:
        for key, value in row.items():
            ep_cols[key].append(value)
    pq.write_table(pa.Table.from_pydict(ep_cols), meta / "episodes" / "chunk-000" / "file-000.parquet")


def convert(dataset_dir: Path, output_root: Path, overwrite: bool) -> None:
    manifest = json.loads((dataset_dir / "manifest.json").read_text())
    if output_root.exists():
        if not overwrite:
            raise FileExistsError(output_root)
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    all_actions = []
    all_states = []
    all_timestamps = []
    all_frame_indices = []
    all_episode_indices = []
    all_indices = []
    all_task_indices = []
    all_scene_images = []
    all_wrist_images = []
    episode_rows = []
    global_index = 0
    fps = int(manifest["fps"])
    image_shape = list(manifest["image_shape"])

    for episode in manifest["episodes"]:
        ep_idx = int(episode["episode_index"])
        episode_path = dataset_dir / episode["path"]
        data = np.load(episode_path)
        n = int(len(data["action"]))
        start = global_index
        end = global_index + n

        write_video(
            output_root / "videos" / "observation.images.scene" / "chunk-000" / f"file-{ep_idx:03d}.mp4",
            data["observation.images.scene"],
            fps,
        )
        all_scene_images.append(data["observation.images.scene"])
        all_wrist_images.append(data["observation.images.wrist"])
        write_video(
            output_root / "videos" / "observation.images.wrist" / "chunk-000" / f"file-{ep_idx:03d}.mp4",
            data["observation.images.wrist"],
            fps,
        )

        action = data["action"].astype(np.float32)
        state = data["observation.state"].astype(np.float32)
        all_actions.append(action)
        all_states.append(state)
        all_timestamps.append(data["timestamp"].astype(np.float32))
        all_frame_indices.append(data["frame_index"].astype(np.int64))
        all_episode_indices.append(np.full(n, ep_idx, dtype=np.int64))
        all_indices.append(np.arange(start, end, dtype=np.int64))
        all_task_indices.append(np.zeros(n, dtype=np.int64))

        ep_action_stats = stats(action)
        ep_state_stats = stats(state)
        row: dict[str, object] = {
            "episode_index": ep_idx,
            "tasks": [TASK],
            "length": n,
            "data/chunk_index": 0,
            "data/file_index": 0,
            "dataset_from_index": start,
            "dataset_to_index": end,
            "videos/observation.images.wrist/chunk_index": 0,
            "videos/observation.images.wrist/file_index": ep_idx,
            "videos/observation.images.wrist/from_timestamp": 0.0,
            "videos/observation.images.wrist/to_timestamp": float((n - 1) / fps),
            "videos/observation.images.scene/chunk_index": 0,
            "videos/observation.images.scene/file_index": ep_idx,
            "videos/observation.images.scene/from_timestamp": 0.0,
            "videos/observation.images.scene/to_timestamp": float((n - 1) / fps),
        }
        for prefix, st in [("stats/action", ep_action_stats), ("stats/observation.state", ep_state_stats)]:
            for key, value in st.items():
                row[f"{prefix}/{key}"] = value
        episode_rows.append(row)
        global_index = end

    rows = {
        "action": np.concatenate(all_actions, axis=0),
        "state": np.concatenate(all_states, axis=0),
        "timestamp": np.concatenate(all_timestamps, axis=0),
        "frame_index": np.concatenate(all_frame_indices, axis=0),
        "episode_index": np.concatenate(all_episode_indices, axis=0),
        "index": np.concatenate(all_indices, axis=0),
        "task_index": np.concatenate(all_task_indices, axis=0),
    }
    image_rows = {
        "scene": np.concatenate(all_scene_images, axis=0),
        "wrist": np.concatenate(all_wrist_images, axis=0),
    }
    write_main_parquet(output_root, rows)
    write_meta(output_root, manifest, rows, episode_rows, image_rows, image_shape, fps)
    print(json.dumps({"output_root": str(output_root), "episodes": len(episode_rows), "frames": int(len(rows["action"]))}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    convert(args.dataset_dir, args.output_root, args.overwrite)


if __name__ == "__main__":
    main()
