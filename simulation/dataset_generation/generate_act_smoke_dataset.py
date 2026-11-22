"""Generate a compact image/state/action dataset for ACT smoke tests.

This is not full LeRobot parquet/video yet. It is a dependency-light bridge:

- stores two RGB camera streams as uint8 arrays in NPZ
- stores robot state and action arrays
- keeps the same scripted expert used by the state-based BC baseline

The goal is to validate the image-observation training path before spending
time on a full ACT/LeRobot conversion.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DEPS = REPO_ROOT / ".sim_deps"
if SIM_DEPS.exists() and str(SIM_DEPS) not in sys.path:
    sys.path.insert(0, str(SIM_DEPS))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from simulation.dataset_generation.generate_expert_dataset import ExpertConfig, SO101CubeExpert
from simulation.environments.soarm101_cube_pick_env import CubePickConfig, SOArm101CubePickEnv


def generate_dataset(output_dir: Path, episodes: int, seed: int, image_size: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    episode_dir = output_dir / "episodes"
    episode_dir.mkdir(parents=True, exist_ok=True)

    env = SOArm101CubePickEnv(
        CubePickConfig(image_width=image_size, image_height=image_size),
        seed=seed,
    )
    expert = SO101CubeExpert(
        env,
        ExpertConfig(use_grasp_assist=True, use_release_assist=True),
    )
    episode_lengths: list[int] = []

    for episode_index in range(episodes):
        obs = env.reset()
        commands = expert.plan_episode()

        states = []
        scene_images = []
        wrist_images = []
        cube_positions = []
        ee_positions = []
        actions = []
        successes = []

        for command in commands:
            states.append(obs["observation.state"])
            scene_images.append(obs["observation.images.scene"])
            wrist_images.append(obs["observation.images.wrist"])
            cube_positions.append(obs["state"]["cube_position"])
            ee_positions.append(obs["state"]["ee_position"])
            actions.append(command.action.astype(np.float32))

            obs, _reward, terminated, _truncated, info = env.step(command.action)
            if command.grasp_assist and expert.config.use_grasp_assist:
                expert.apply_grasp_assist()
                obs = env._get_observation()
                terminated = bool(obs["state"]["cube_position"][2] > 0.08)
                info = {"is_success": terminated, "grasp_assist": True}
            elif command.release and expert.config.use_release_assist:
                expert.apply_release_assist()
                obs = env._get_observation()
            successes.append(bool(info["is_success"] or terminated))

        frame_count = len(actions)
        episode_lengths.append(frame_count)
        np.savez_compressed(
            episode_dir / f"episode_{episode_index:06d}.npz",
            **{
                "observation.state": np.asarray(states, dtype=np.float32),
                "observation.images.scene": np.asarray(scene_images, dtype=np.uint8),
                "observation.images.wrist": np.asarray(wrist_images, dtype=np.uint8),
                "cube_position": np.asarray(cube_positions, dtype=np.float32),
                "ee_position": np.asarray(ee_positions, dtype=np.float32),
                "action": np.asarray(actions, dtype=np.float32),
                "success": np.asarray(successes, dtype=np.bool_),
                "timestamp": np.arange(frame_count, dtype=np.float32) / env.config.fps,
                "frame_index": np.arange(frame_count, dtype=np.int64),
                "episode_index": np.full(frame_count, episode_index, dtype=np.int64),
            },
        )

    env.close()
    meta = {
        "codebase_version": "act-smoke-npz-v1",
        "robot_type": "so101",
        "task": "SO-101 pick cube in MuJoCo",
        "total_episodes": episodes,
        "total_frames": int(sum(episode_lengths)),
        "episode_lengths": episode_lengths,
        "image_size": image_size,
        "features": {
            "observation.images.scene": {"dtype": "uint8", "shape": [image_size, image_size, 3]},
            "observation.images.wrist": {"dtype": "uint8", "shape": [image_size, image_size, 3]},
            "observation.state": {"dtype": "float32", "shape": [6]},
            "action": {"dtype": "float32", "shape": [6]},
        },
        "note": "Compact NPZ image dataset for local ACT smoke tests; not full LeRobot parquet/video.",
    }
    meta_dir = output_dir / "meta"
    meta_dir.mkdir(exist_ok=True)
    (meta_dir / "info.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--image-size", type=int, default=64)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    generate_dataset(args.output_dir, args.episodes, args.seed, args.image_size)
    print(f"generated={args.output_dir}")


if __name__ == "__main__":
    main()
