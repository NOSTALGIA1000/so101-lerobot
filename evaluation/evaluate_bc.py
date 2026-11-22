"""Evaluate the lightweight BC baseline in the MuJoCo cube-pick environment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SIM_DEPS = REPO_ROOT / ".sim_deps"
if SIM_DEPS.exists() and str(SIM_DEPS) not in sys.path:
    sys.path.insert(0, str(SIM_DEPS))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from simulation.environments.soarm101_cube_pick_env import SOArm101CubePickEnv


class BCPolicy:
    def __init__(self, checkpoint: Path) -> None:
        data = np.load(checkpoint)
        self.w1 = data["w1"]
        self.b1 = data["b1"]
        self.w2 = data["w2"]
        self.b2 = data["b2"]
        self.w3 = data["w3"]
        self.b3 = data["b3"]
        self.x_mean = data["x_mean"]
        self.x_std = data["x_std"]

    def predict(self, obs: dict[str, object], phase: float) -> np.ndarray:
        state = obs["observation.state"].astype(np.float32)
        cube = obs["state"]["cube_position"].astype(np.float32)
        x = np.concatenate([state, cube, np.array([phase], dtype=np.float32)], axis=0)[None, :]
        x = (x - self.x_mean) / self.x_std
        h1 = np.maximum(x @ self.w1 + self.b1, 0.0)
        h2 = np.maximum(h1 @ self.w2 + self.b2, 0.0)
        return (h2 @ self.w3 + self.b3)[0].astype(np.float32)


def evaluate(args: argparse.Namespace) -> dict[str, object]:
    policy = BCPolicy(args.policy)
    successes = []
    max_heights = []
    episode_lengths = []

    for episode in range(args.episodes):
        env = SOArm101CubePickEnv(seed=args.seed + episode)
        obs = env.reset()
        success = False
        max_height = float(obs["state"]["cube_position"][2])
        steps = 0
        for step in range(args.max_steps):
            phase = step / max(float(args.max_steps - 1), 1.0)
            action = policy.predict(obs, phase)
            obs, _reward, terminated, _truncated, info = env.step(action)
            max_height = max(max_height, float(obs["state"]["cube_position"][2]))
            steps = step + 1
            if terminated or info.get("is_success", False):
                success = True
                break
        env.close()
        successes.append(success)
        max_heights.append(max_height)
        episode_lengths.append(steps)

    return {
        "policy": str(args.policy),
        "episodes": args.episodes,
        "success_rate": float(np.mean(successes)),
        "successes": successes,
        "mean_max_cube_height": float(np.mean(max_heights)),
        "max_cube_heights": max_heights,
        "mean_episode_length": float(np.mean(episode_lengths)),
        "episode_lengths": episode_lengths,
        "note": "State+cube-position+phase BC baseline. This is not yet a camera-observation policy.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=REPO_ROOT / "training" / "outputs" / "bc_state_cube_policy.npz")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "evaluation" / "evaluation_result.json")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--max-steps", type=int, default=280)
    parser.add_argument("--seed", type=int, default=100)
    args = parser.parse_args()

    result = evaluate(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
