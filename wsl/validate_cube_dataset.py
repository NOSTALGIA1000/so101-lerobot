#!/usr/bin/env python3
import json
from pathlib import Path

from lerobot.datasets.lerobot_dataset import LeRobotDataset


REPO_ID = "local/so101_grasp_cube_test_20260721_200217"
ROOT = Path.home() / "lerobot_data" / "so101_grasp_cube_test_20260721_200217"


def main() -> None:
    info = json.loads((ROOT / "meta" / "info.json").read_text())
    assert info["total_episodes"] == 46, info["total_episodes"]
    assert info["total_frames"] == 19958, info["total_frames"]
    assert info["fps"] == 30, info["fps"]

    camera_keys = sorted(
        key for key in info["features"] if key.startswith("observation.images.")
    )
    assert camera_keys == ["observation.images.scene", "observation.images.wrist"], camera_keys

    dataset = LeRobotDataset(REPO_ID, root=ROOT)
    assert dataset.num_episodes == 46, dataset.num_episodes
    assert len(dataset) == 19958, len(dataset)

    first = dataset[0]
    last = dataset[len(dataset) - 1]
    required = {"observation.state", "action", *camera_keys}
    assert required.issubset(first), sorted(first)
    assert required.issubset(last), sorted(last)

    print(f"repo_id={REPO_ID}")
    print(f"root={ROOT}")
    print(f"episodes={dataset.num_episodes}")
    print(f"frames={len(dataset)}")
    print(f"fps={info['fps']}")
    print(f"cameras={camera_keys}")
    print("dataset_validation=PASS")


if __name__ == "__main__":
    main()
