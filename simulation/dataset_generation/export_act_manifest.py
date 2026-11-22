"""Export a compact ACT smoke NPZ dataset manifest.

The manifest is a dependency-free bridge for WSL/LeRobot conversion. It lists
episode files, feature schema, camera keys, action/state names, and aggregate
stats so the WSL side can convert to LeRobot v3 parquet/video or train through
an adapter dataset.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


ACTION_NAMES = [
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
]


def export_manifest(dataset_dir: Path, output_path: Path) -> dict[str, object]:
    episode_paths = sorted((dataset_dir / "episodes").glob("episode_*.npz"))
    if not episode_paths:
        raise FileNotFoundError(f"No episode_*.npz files found under {dataset_dir / 'episodes'}")

    episodes = []
    action_values = []
    state_values = []
    total_frames = 0
    image_shape = None

    for episode_path in episode_paths:
        data = np.load(episode_path)
        frame_count = int(len(data["action"]))
        total_frames += frame_count
        action_values.append(data["action"].astype(np.float32))
        state_values.append(data["observation.state"].astype(np.float32))
        if image_shape is None:
            image_shape = list(data["observation.images.scene"].shape[1:])
        episodes.append(
            {
                "episode_index": int(data["episode_index"][0]),
                "path": str(episode_path.relative_to(dataset_dir)).replace("\\", "/"),
                "frames": frame_count,
                "success_any": bool(data["success"].any()),
                "scene_shape": list(data["observation.images.scene"].shape),
                "wrist_shape": list(data["observation.images.wrist"].shape),
            },
        )

    actions = np.concatenate(action_values, axis=0)
    states = np.concatenate(state_values, axis=0)
    manifest = {
        "format": "so101_act_smoke_npz_manifest_v1",
        "dataset_dir": str(dataset_dir),
        "robot_type": "so101",
        "fps": 30,
        "total_episodes": len(episodes),
        "total_frames": total_frames,
        "camera_keys": ["observation.images.scene", "observation.images.wrist"],
        "image_shape": image_shape,
        "action_names": ACTION_NAMES,
        "state_names": ACTION_NAMES,
        "features": {
            "observation.images.scene": {"dtype": "uint8", "shape": image_shape},
            "observation.images.wrist": {"dtype": "uint8", "shape": image_shape},
            "observation.state": {"dtype": "float32", "shape": [6], "names": ACTION_NAMES},
            "action": {"dtype": "float32", "shape": [6], "names": ACTION_NAMES},
            "timestamp": {"dtype": "float32", "shape": [1]},
            "frame_index": {"dtype": "int64", "shape": [1]},
            "episode_index": {"dtype": "int64", "shape": [1]},
        },
        "stats": {
            "action_mean": actions.mean(axis=0).tolist(),
            "action_std": actions.std(axis=0).tolist(),
            "action_min": actions.min(axis=0).tolist(),
            "action_max": actions.max(axis=0).tolist(),
            "state_mean": states.mean(axis=0).tolist(),
            "state_std": states.std(axis=0).tolist(),
            "state_min": states.min(axis=0).tolist(),
            "state_max": states.max(axis=0).tolist(),
        },
        "episodes": episodes,
        "next_conversion_target": "LeRobot v3 parquet/video",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = export_manifest(args.dataset_dir, args.output)
    print(json.dumps({k: manifest[k] for k in ["format", "total_episodes", "total_frames", "image_shape"]}, indent=2))


if __name__ == "__main__":
    main()
