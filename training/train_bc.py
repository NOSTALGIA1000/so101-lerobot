"""Train a lightweight behavior cloning policy on simulated SO-101 data.

This is a dependency-light baseline for the simulation pipeline. It uses NumPy
only and trains a small MLP on:

  observation.state + cube_position + phase -> action

The visual ACT/Diffusion training path should replace this once the generated
dataset is converted to full LeRobot parquet/video format.
"""

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


def load_dataset(dataset_dir: Path, truncate_at_success: bool = False) -> tuple[np.ndarray, np.ndarray]:
    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    for episode_path in sorted((dataset_dir / "episodes").glob("episode_*.npz")):
        data = np.load(episode_path)
        state = data["observation.state"].astype(np.float32)
        cube = data["cube_position"].astype(np.float32)
        action = data["action"].astype(np.float32)
        if truncate_at_success and "success" in data.files:
            success_indices = np.flatnonzero(data["success"].astype(bool))
            if len(success_indices) > 0:
                end = int(success_indices[0]) + 1
                state = state[:end]
                cube = cube[:end]
                action = action[:end]
        frame_index = data["frame_index"].astype(np.float32)[:, None]
        frame_index = frame_index[: len(action)]
        phase = frame_index / max(float(len(frame_index) - 1), 1.0)
        xs.append(np.concatenate([state, cube, phase], axis=1))
        ys.append(action)
    if not xs:
        raise FileNotFoundError(f"No episode_*.npz files found under {dataset_dir / 'episodes'}")
    return np.concatenate(xs, axis=0), np.concatenate(ys, axis=0)


class Normalizer:
    def __init__(self, x: np.ndarray) -> None:
        self.mean = x.mean(axis=0, keepdims=True)
        self.std = x.std(axis=0, keepdims=True) + 1e-6

    def encode(self, x: np.ndarray) -> np.ndarray:
        return (x - self.mean) / self.std

    def to_dict(self) -> dict[str, list[list[float]]]:
        return {"mean": self.mean.tolist(), "std": self.std.tolist()}


class MLP:
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, rng: np.random.Generator) -> None:
        scale1 = np.sqrt(2.0 / input_dim)
        scale2 = np.sqrt(2.0 / hidden_dim)
        self.w1 = rng.normal(0.0, scale1, size=(input_dim, hidden_dim)).astype(np.float32)
        self.b1 = np.zeros((1, hidden_dim), dtype=np.float32)
        self.w2 = rng.normal(0.0, scale2, size=(hidden_dim, hidden_dim)).astype(np.float32)
        self.b2 = np.zeros((1, hidden_dim), dtype=np.float32)
        self.w3 = rng.normal(0.0, 0.01, size=(hidden_dim, output_dim)).astype(np.float32)
        self.b3 = np.zeros((1, output_dim), dtype=np.float32)

        self.m = {name: np.zeros_like(value) for name, value in self.params().items()}
        self.v = {name: np.zeros_like(value) for name, value in self.params().items()}
        self.t = 0

    def params(self) -> dict[str, np.ndarray]:
        return {
            "w1": self.w1,
            "b1": self.b1,
            "w2": self.w2,
            "b2": self.b2,
            "w3": self.w3,
            "b3": self.b3,
        }

    def forward(self, x: np.ndarray) -> tuple[np.ndarray, tuple[np.ndarray, ...]]:
        z1 = x @ self.w1 + self.b1
        h1 = np.maximum(z1, 0.0)
        z2 = h1 @ self.w2 + self.b2
        h2 = np.maximum(z2, 0.0)
        y = h2 @ self.w3 + self.b3
        return y, (x, z1, h1, z2, h2)

    def train_step(self, x: np.ndarray, y_true: np.ndarray, lr: float) -> float:
        y_pred, cache = self.forward(x)
        diff = y_pred - y_true
        loss = float(np.mean(diff * diff))
        grad = (2.0 / y_true.shape[0]) * diff
        x0, z1, h1, z2, h2 = cache

        grads: dict[str, np.ndarray] = {}
        grads["w3"] = h2.T @ grad
        grads["b3"] = grad.sum(axis=0, keepdims=True)
        dh2 = grad @ self.w3.T
        dz2 = dh2 * (z2 > 0.0)
        grads["w2"] = h1.T @ dz2
        grads["b2"] = dz2.sum(axis=0, keepdims=True)
        dh1 = dz2 @ self.w2.T
        dz1 = dh1 * (z1 > 0.0)
        grads["w1"] = x0.T @ dz1
        grads["b1"] = dz1.sum(axis=0, keepdims=True)

        self._adam_update(grads, lr)
        return loss

    def _adam_update(self, grads: dict[str, np.ndarray], lr: float) -> None:
        self.t += 1
        beta1 = 0.9
        beta2 = 0.999
        eps = 1e-8
        for name, param in self.params().items():
            grad = grads[name].astype(np.float32)
            self.m[name] = beta1 * self.m[name] + (1.0 - beta1) * grad
            self.v[name] = beta2 * self.v[name] + (1.0 - beta2) * (grad * grad)
            m_hat = self.m[name] / (1.0 - beta1**self.t)
            v_hat = self.v[name] / (1.0 - beta2**self.t)
            param -= lr * m_hat / (np.sqrt(v_hat) + eps)

    def save(self, path: Path, normalizer: Normalizer, metadata: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, **self.params(), x_mean=normalizer.mean, x_std=normalizer.std)
        (path.with_suffix(".json")).write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def train(args: argparse.Namespace) -> None:
    x, y = load_dataset(args.dataset_dir, truncate_at_success=args.truncate_at_success)
    rng = np.random.default_rng(args.seed)
    indices = rng.permutation(len(x))
    split = max(1, int(len(indices) * (1.0 - args.val_ratio)))
    train_idx = indices[:split]
    val_idx = indices[split:] if split < len(indices) else indices[:1]

    normalizer = Normalizer(x[train_idx])
    x_train = normalizer.encode(x[train_idx])
    y_train = y[train_idx]
    x_val = normalizer.encode(x[val_idx])
    y_val = y[val_idx]

    model = MLP(x_train.shape[1], args.hidden_dim, y_train.shape[1], rng)

    for step in range(1, args.steps + 1):
        batch_idx = rng.choice(len(x_train), size=args.batch_size, replace=len(x_train) < args.batch_size)
        loss = model.train_step(x_train[batch_idx], y_train[batch_idx], args.lr)
        if step == 1 or step % args.log_freq == 0 or step == args.steps:
            pred, _ = model.forward(x_val)
            val_loss = float(np.mean((pred - y_val) ** 2))
            print(f"step={step} train_loss={loss:.6f} val_loss={val_loss:.6f}")

    metadata = {
        "dataset_dir": str(args.dataset_dir),
        "input": "observation.state + cube_position + phase",
        "output": "action",
        "input_dim": int(x_train.shape[1]),
        "action_dim": int(y_train.shape[1]),
        "steps": args.steps,
        "hidden_dim": args.hidden_dim,
        "train_samples": int(len(x_train)),
        "val_samples": int(len(x_val)),
        "truncate_at_success": bool(args.truncate_at_success),
    }
    model.save(args.output_path, normalizer, metadata)
    print(f"saved={args.output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, default=REPO_ROOT / "simulation" / "outputs" / "expert_dataset_smoke_v4")
    parser.add_argument("--output-path", type=Path, default=REPO_ROOT / "training" / "outputs" / "bc_state_cube_policy.npz")
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--log-freq", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--truncate-at-success", action="store_true")
    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
