"""Train a lightweight chunked behavior cloning policy.

This is an ACT-style debugging baseline without transformers:

  observation.state + cube_position + phase -> action_chunk

The checkpoint stores a small NumPy MLP that predicts `chunk_size` future
actions. Evaluation can execute the chunk open-loop before querying again.
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


def load_dataset(dataset_dir: Path, chunk_size: int, use_ee_position: bool = True) -> tuple[np.ndarray, np.ndarray, int, bool]:
    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    action_dim = 0
    for episode_path in sorted((dataset_dir / "episodes").glob("episode_*.npz")):
        data = np.load(episode_path)
        state = data["observation.state"].astype(np.float32)
        cube = data["cube_position"].astype(np.float32)
        ee = data["ee_position"].astype(np.float32) if use_ee_position and "ee_position" in data.files else None
        action = data["action"].astype(np.float32)
        action_dim = action.shape[1]
        frame_index = data["frame_index"].astype(np.float32)[:, None]
        phase = frame_index / max(float(len(frame_index) - 1), 1.0)
        if ee is not None:
            x = np.concatenate([state, cube, ee, phase], axis=1)
        else:
            x = np.concatenate([state, cube, phase], axis=1)

        chunks = []
        for idx in range(len(action)):
            end = min(idx + chunk_size, len(action))
            chunk = np.zeros((chunk_size, action_dim), dtype=np.float32)
            chunk[: end - idx] = action[idx:end]
            if end - idx < chunk_size:
                chunk[end - idx :] = action[-1]
            chunks.append(chunk.reshape(-1))
        xs.append(x)
        ys.append(np.asarray(chunks, dtype=np.float32))
    if not xs:
        raise FileNotFoundError(f"No episode_*.npz files found under {dataset_dir / 'episodes'}")
    return np.concatenate(xs, axis=0), np.concatenate(ys, axis=0), action_dim, xs[0].shape[1] == 13


class Normalizer:
    def __init__(self, x: np.ndarray) -> None:
        self.mean = x.mean(axis=0, keepdims=True)
        self.std = x.std(axis=0, keepdims=True) + 1e-6

    def encode(self, x: np.ndarray) -> np.ndarray:
        return (x - self.mean) / self.std


class MLP:
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, rng: np.random.Generator) -> None:
        self.w1 = rng.normal(0.0, np.sqrt(2.0 / input_dim), size=(input_dim, hidden_dim)).astype(np.float32)
        self.b1 = np.zeros((1, hidden_dim), dtype=np.float32)
        self.w2 = rng.normal(0.0, np.sqrt(2.0 / hidden_dim), size=(hidden_dim, hidden_dim)).astype(np.float32)
        self.b2 = np.zeros((1, hidden_dim), dtype=np.float32)
        self.w3 = rng.normal(0.0, 0.01, size=(hidden_dim, output_dim)).astype(np.float32)
        self.b3 = np.zeros((1, output_dim), dtype=np.float32)
        self.m = {name: np.zeros_like(value) for name, value in self.params().items()}
        self.v = {name: np.zeros_like(value) for name, value in self.params().items()}
        self.t = 0

    def params(self) -> dict[str, np.ndarray]:
        return {"w1": self.w1, "b1": self.b1, "w2": self.w2, "b2": self.b2, "w3": self.w3, "b3": self.b3}

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
        grads = {
            "w3": h2.T @ grad,
            "b3": grad.sum(axis=0, keepdims=True),
        }
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
        path.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def train(args: argparse.Namespace) -> None:
    x, y, action_dim, used_ee_position = load_dataset(
        args.dataset_dir,
        args.chunk_size,
        use_ee_position=not args.no_ee_position,
    )
    rng = np.random.default_rng(args.seed)
    indices = rng.permutation(len(x))
    split = max(1, int(len(indices) * (1.0 - args.val_ratio)))
    train_idx = indices[:split]
    val_idx = indices[split:] if split < len(indices) else indices[:1]
    normalizer = Normalizer(x[train_idx])
    x_train = normalizer.encode(x[train_idx])
    x_val = normalizer.encode(x[val_idx])
    y_train = y[train_idx]
    y_val = y[val_idx]
    model = MLP(x_train.shape[1], args.hidden_dim, y_train.shape[1], rng)

    for step in range(1, args.steps + 1):
        batch_idx = rng.choice(len(x_train), size=args.batch_size, replace=len(x_train) < args.batch_size)
        loss = model.train_step(x_train[batch_idx], y_train[batch_idx], args.lr)
        if step == 1 or step % args.log_freq == 0 or step == args.steps:
            pred, _ = model.forward(x_val)
            val_loss = float(np.mean((pred - y_val) ** 2))
            print(f"step={step} train_loss={loss:.6f} val_loss={val_loss:.6f}")

    model.save(
        args.output_path,
        normalizer,
        {
            "dataset_dir": str(args.dataset_dir),
            "input": "observation.state + cube_position + ee_position + phase"
            if used_ee_position
            else "observation.state + cube_position + phase",
            "output": "action_chunk",
            "input_dim": int(x_train.shape[1]),
            "action_dim": int(action_dim),
            "use_ee_position": bool(used_ee_position),
            "chunk_size": int(args.chunk_size),
            "steps": int(args.steps),
            "hidden_dim": int(args.hidden_dim),
            "train_samples": int(len(x_train)),
            "val_samples": int(len(x_val)),
        },
    )
    print(f"saved={args.output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--chunk-size", type=int, default=10)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--log-freq", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--no-ee-position", action="store_true")
    train(parser.parse_args())


if __name__ == "__main__":
    main()
