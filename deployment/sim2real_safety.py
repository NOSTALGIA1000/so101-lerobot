"""Safety utilities for SO-101 sim-to-real policy dry-runs.

This module deliberately does not connect to the real robot. It loads a trained
chunked policy, validates action dimensionality, clips actions to the SO-101
joint limits, and applies per-step rate limits. The output can be inspected
before wiring it into the LeRobot follower runtime.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SIM_DEPS = REPO_ROOT / ".sim_deps"
if SIM_DEPS.exists() and str(SIM_DEPS) not in sys.path:
    sys.path.insert(0, str(SIM_DEPS))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.evaluate_chunk_bc import ChunkBCPolicy
from simulation.robots.soarm101 import SOARM101


@dataclass(frozen=True)
class SafetyConfig:
    """Conservative limits for first sim-to-real dry-runs."""

    max_delta_per_step: tuple[float, ...] = (0.035, 0.035, 0.035, 0.035, 0.05, 0.08)
    neutral_action: tuple[float, ...] = (0.0, -0.7, 0.7, 0.0, 0.0, 1.2)

    @property
    def action_dim(self) -> int:
        return len(self.neutral_action)


class SafeActionFilter:
    def __init__(self, config: SafetyConfig | None = None) -> None:
        self.config = config or SafetyConfig()
        self.lower = np.array([joint.lower for joint in SOARM101.joint_specs], dtype=np.float32)
        self.upper = np.array([joint.upper for joint in SOARM101.joint_specs], dtype=np.float32)
        self.max_delta = np.asarray(self.config.max_delta_per_step, dtype=np.float32)
        self.previous = np.asarray(self.config.neutral_action, dtype=np.float32)
        if self.previous.shape != (SOARM101.action_dim,):
            raise ValueError(f"Neutral action must have shape {(SOARM101.action_dim,)}, got {self.previous.shape}")

    def reset(self, action: np.ndarray | None = None) -> np.ndarray:
        if action is None:
            action = np.asarray(self.config.neutral_action, dtype=np.float32)
        self.previous = self.clip(action)
        return self.previous.copy()

    def clip(self, action: np.ndarray) -> np.ndarray:
        action = np.asarray(action, dtype=np.float32)
        if action.shape != (SOARM101.action_dim,):
            raise ValueError(f"Expected action shape {(SOARM101.action_dim,)}, got {action.shape}")
        return np.clip(action, self.lower, self.upper)

    def filter(self, action: np.ndarray) -> np.ndarray:
        clipped = self.clip(action)
        delta = np.clip(clipped - self.previous, -self.max_delta, self.max_delta)
        safe = self.clip(self.previous + delta)
        self.previous = safe
        return safe.copy()


def fake_observation(phase: float) -> dict[str, object]:
    """Create a deterministic fake observation for policy dry-run checks."""

    neutral = np.asarray(SafetyConfig().neutral_action, dtype=np.float32)
    cube = np.array([0.22, 0.0, 0.03], dtype=np.float32)
    return {
        "observation.state": neutral,
        "state": {
            "cube_position": cube + np.array([0.02 * np.sin(phase * np.pi), 0.0, 0.0], dtype=np.float32),
            "ee_position": np.array([0.22, 0.0, 0.10], dtype=np.float32),
        },
    }


def run_dry_run(policy_path: Path, steps: int, execute_chunk: int) -> dict[str, object]:
    policy = ChunkBCPolicy(policy_path)
    action_filter = SafeActionFilter()
    safe_actions = []
    raw_actions = []

    step = 0
    while step < steps:
        phase = step / max(float(steps - 1), 1.0)
        obs = fake_observation(phase)
        chunk = policy.predict_chunk(obs, phase)
        for action in chunk[:execute_chunk]:
            raw_actions.append(action.astype(np.float32))
            safe_actions.append(action_filter.filter(action))
            step += 1
            if step >= steps:
                break

    raw = np.asarray(raw_actions, dtype=np.float32)
    safe = np.asarray(safe_actions, dtype=np.float32)
    return {
        "policy": str(policy_path),
        "steps": int(len(safe)),
        "execute_chunk": int(execute_chunk),
        "action_names": list(SOARM101.action_keys),
        "joint_limits_lower": action_filter.lower.tolist(),
        "joint_limits_upper": action_filter.upper.tolist(),
        "raw_min": raw.min(axis=0).tolist(),
        "raw_max": raw.max(axis=0).tolist(),
        "safe_min": safe.min(axis=0).tolist(),
        "safe_max": safe.max(axis=0).tolist(),
        "max_safe_delta": np.abs(np.diff(safe, axis=0)).max(axis=0).tolist() if len(safe) > 1 else [0.0] * safe.shape[1],
        "first_safe_action": safe[0].tolist(),
        "last_safe_action": safe[-1].tolist(),
        "note": "Dry-run only. This does not connect to hardware.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "deployment" / "outputs" / "sim2real_dry_run.json")
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--execute-chunk", type=int, default=10)
    args = parser.parse_args()

    result = run_dry_run(args.policy, args.steps, args.execute_chunk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
