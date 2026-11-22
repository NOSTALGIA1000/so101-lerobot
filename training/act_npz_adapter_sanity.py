"""Sanity-check compact NPZ ACT samples without PyTorch/LeRobot dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


class ActNpzAdapter:
    def __init__(self, dataset_dir: Path, chunk_size: int = 10) -> None:
        self.dataset_dir = dataset_dir
        self.chunk_size = chunk_size
        self.manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
        self.episodes = self.manifest["episodes"]
        self.index: list[tuple[int, int]] = []
        for episode_idx, episode in enumerate(self.episodes):
            for frame_idx in range(int(episode["frames"])):
                self.index.append((episode_idx, frame_idx))

    def __len__(self) -> int:
        return len(self.index)

    def __getitem__(self, idx: int) -> dict[str, np.ndarray]:
        episode_idx, frame_idx = self.index[idx]
        episode_path = self.dataset_dir / self.episodes[episode_idx]["path"]
        data = np.load(episode_path)
        actions = data["action"].astype(np.float32)
        end = min(frame_idx + self.chunk_size, len(actions))
        chunk = np.zeros((self.chunk_size, actions.shape[1]), dtype=np.float32)
        chunk[: end - frame_idx] = actions[frame_idx:end]
        if end - frame_idx < self.chunk_size:
            chunk[end - frame_idx :] = actions[-1]
        return {
            "observation.images.scene": data["observation.images.scene"][frame_idx],
            "observation.images.wrist": data["observation.images.wrist"][frame_idx],
            "observation.state": data["observation.state"][frame_idx].astype(np.float32),
            "action": chunk,
            "episode_index": np.array(episode_idx, dtype=np.int64),
            "frame_index": np.array(frame_idx, dtype=np.int64),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--chunk-size", type=int, default=10)
    args = parser.parse_args()
    dataset = ActNpzAdapter(args.dataset_dir, args.chunk_size)
    first = dataset[0]
    middle = dataset[len(dataset) // 2]
    last = dataset[len(dataset) - 1]
    summary = {
        "dataset_dir": str(args.dataset_dir),
        "samples": len(dataset),
        "chunk_size": args.chunk_size,
        "first": {k: list(v.shape) for k, v in first.items()},
        "middle": {k: list(v.shape) for k, v in middle.items()},
        "last": {k: list(v.shape) for k, v in last.items()},
        "status": "PASS",
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
