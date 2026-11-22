#!/usr/bin/env python3
"""
Offline checkpoint evaluator — no robot needed.

Loads checkpoints, runs inference on eval split, ranks by metrics.
Output: eval_ranking.json sorted by eval_loss.

Usage:
  python wsl/eval_checkpoints.py                          # all FT checkpoints
  python wsl/eval_checkpoints.py --ckpts /path/ckpt1 /path/ckpt2
  python wsl/eval_checkpoints.py --output ranking.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from lerobot.datasets.lerobot_dataset import LeRobotDataset

JOINT_NAMES = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]


def load_policy(ckpt_path: str):
    """Load ACT policy from checkpoint. Returns (policy, preprocessor, device)."""
    from lerobot.policies.act.modeling_act import ACTPolicy
    from lerobot.policies.factory import make_pre_post_processors

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    policy = ACTPolicy.from_pretrained(ckpt_path).to(device).eval()
    preprocessor, _ = make_pre_post_processors(
        policy_cfg=policy.config,
        pretrained_path=ckpt_path,
        preprocessor_overrides={"device_processor": {"device": str(device)}},
    )
    return policy, preprocessor, device


def load_eval_dataloader(dataset_root: str, repo_id: str, batch_size: int = 8):
    """Load eval split of dataset. Uses 0.15 random split matching training."""
    from lerobot.datasets.lerobot_dataset import LeRobotDataset

    dataset = LeRobotDataset(repo_id, root=dataset_root)
    n_eval = max(1, int(dataset.num_episodes * 0.15))
    eval_from = dataset.num_episodes - n_eval

    eval_indices = list(range(
        dataset.meta.episodes[eval_from]["dataset_from_index"],
        dataset.meta.episodes[dataset.num_episodes - 1]["dataset_to_index"],
    ))

    # Force eval_split so the dataset object uses eval transform
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        sampler=eval_indices,
        num_workers=2,
        drop_last=False,
    )
    return loader, n_eval


def evaluate_checkpoint(ckpt_path: str, dataloader, policy, preprocessor, device, action_mean: np.ndarray, action_std: np.ndarray) -> dict:
    """Run inference on eval split and compute metrics.

    Loss computed in normalized space (matches training eval_loss).
    MAE/MSE converted to degrees using dataset action stats.
    """
    import torch.nn.functional as F

    policy.reset()

    all_preds_norm = []
    all_targets_norm = []
    total_loss = 0.0
    n_samples = 0

    mean_t = torch.tensor(action_mean, dtype=torch.float32, device=device)
    std_t = torch.tensor(action_std, dtype=torch.float32, device=device)

    with torch.inference_mode():
        for batch in dataloader:
            batch = preprocessor(batch)
            targets = batch["action"].to(device)

            # Deterministic inference: predict action chunk, take first step
            pred_chunk = policy.select_action(batch)  # [B, 6] or [B, chunk_size, 6]
            if pred_chunk.dim() == 3:
                pred = pred_chunk[:, 0, :]
            else:
                pred = pred_chunk

            # Handle batch size mismatch (last batch may be partial)
            bs = min(len(pred), len(targets))
            pred = pred[:bs]
            targets = targets[:bs]

            # Loss in normalized space
            loss = F.l1_loss(pred, targets)
            total_loss += loss.item() * bs
            n_samples += bs

            # Convert to degrees: deg = norm * std + mean
            pred_deg = pred * std_t + mean_t
            targets_deg = targets * std_t + mean_t

            all_targets_norm.append(targets_deg.detach().cpu().numpy())
            all_preds_norm.append(pred_deg.detach().cpu().numpy())

    targets = np.concatenate(all_targets_norm, axis=0)
    preds = np.concatenate(all_preds_norm, axis=0)

    eval_loss = total_loss / max(n_samples, 1)
    errors = preds - targets  # shape: [N, 6]

    mse_per_joint = (errors ** 2).mean(axis=0).tolist()
    mae_per_joint = np.abs(errors).mean(axis=0).tolist()
    max_ae_per_joint = np.abs(errors).max(axis=0).tolist()

    tgt_var = targets.var(axis=0)
    pred_var = preds.var(axis=0)
    var_ratio = (pred_var / (tgt_var + 1e-8)).tolist()

    return {
        "eval_loss": round(float(eval_loss), 6),
        "mse_per_joint": {name: round(v, 6) for name, v in zip(JOINT_NAMES, mse_per_joint)},
        "mae_per_joint": {name: round(v, 4) for name, v in zip(JOINT_NAMES, mae_per_joint)},
        "max_ae_per_joint": {name: round(v, 4) for name, v in zip(JOINT_NAMES, max_ae_per_joint)},
        "var_ratio": {name: round(v, 4) for name, v in zip(JOINT_NAMES, var_ratio)},
        "n_samples": int(n_samples),
    }


def find_checkpoints(base_dir: str) -> list[str]:
    """Auto-discover checkpoints in output directories."""
    from pathlib import Path

    root = Path(base_dir)
    ckpts = []
    for run_dir in sorted(root.iterdir()):
        if not run_dir.is_dir():
            continue
        ckpt_dir = run_dir / "checkpoints"
        if not ckpt_dir.is_dir():
            continue
        for step_dir in sorted(ckpt_dir.iterdir()):
            pt_dir = step_dir / "pretrained_model"
            if pt_dir.is_dir() and (pt_dir / "model.safetensors").exists():
                ckpts.append(str(pt_dir))
    return ckpts


def main():
    parser = argparse.ArgumentParser(description="Evaluate checkpoints offline")
    parser.add_argument("--ckpts", nargs="*", default=None,
                        help="Checkpoint paths (auto-discover if omitted)")
    parser.add_argument("--dataset-root", default=None,
                        help="Real dataset root (default: $HOME/lerobot_data/so101_real_cube_pick_img64)")
    parser.add_argument("--repo-id", default="local/so101_real_cube_pick_img64")
    parser.add_argument("--output", default=None,
                        help="Output JSON path (default: eval_ranking.json in cwd)")
    parser.add_argument("--output-dir", default=None,
                        help="Scan directory for auto-discover")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    home = Path.home()
    dataset_root = args.dataset_root or str(home / "lerobot_data" / "so101_real_cube_pick_img64")

    # Auto-discover checkpoints
    if args.ckpts:
        ckpt_paths = args.ckpts
    elif args.output_dir:
        ckpt_paths = find_checkpoints(args.output_dir)
    else:
        # Scan standard output locations
        all_ckpts = find_checkpoints(str(home / "lerobot_outputs"))
        ckpt_paths = [c for c in all_ckpts if "act_real_ft_" in c or "act_real_finetune" in c]

    if not ckpt_paths:
        print("No checkpoints found. Specify --ckpts or --output-dir.")
        sys.exit(1)

    print(f"Found {len(ckpt_paths)} checkpoints:")
    for c in ckpt_paths:
        print(f"  {c}")
    print()

    # Load dataset once
    print(f"Loading eval dataset: {dataset_root}")
    dataset = LeRobotDataset(args.repo_id, root=dataset_root)

    # Load action stats for degree conversion
    import json
    meta_dir = Path(dataset_root) / "meta"
    stats_path = meta_dir / "stats.json"
    if not stats_path.exists():
        stats_path = meta_dir / "info.json"
    with open(stats_path) as f:
        stats = json.load(f)
    action_mean = np.array(stats["action"]["mean"])
    action_std = np.array(stats["action"]["std"])
    print(f"  action stats loaded: mean={action_mean[:3]}..., std={action_std[:3]}...")

    n_eval = max(1, int(dataset.num_episodes * 0.15))
    eval_from = dataset.num_episodes - n_eval
    eval_indices = list(range(
        dataset.meta.episodes[eval_from]["dataset_from_index"],
        dataset.meta.episodes[dataset.num_episodes - 1]["dataset_to_index"],
    ))
    print(f"  episodes={dataset.num_episodes}, eval split: {n_eval} episodes ({len(eval_indices)} frames)")
    dataloader = DataLoader(
        dataset, batch_size=args.batch_size, sampler=eval_indices,
        num_workers=2, drop_last=False,
    )

    results = []
    for ckpt_path in ckpt_paths:
        print(f"\nEvaluating: {Path(ckpt_path).parent.parent.name}/{Path(ckpt_path).parent.name} ...")
        policy = None  # ensure GC
        try:
            policy, preprocessor, device = load_policy(ckpt_path)
        except Exception as e:
            print(f"  ERROR loading policy: {e}")
            results.append({"checkpoint": ckpt_path, "error": str(e)})
            continue

        try:
            metrics = evaluate_checkpoint(ckpt_path, dataloader, policy, preprocessor, device, action_mean, action_std)
            metrics["checkpoint"] = ckpt_path
            results.append(metrics)
            print(f"  eval_loss={metrics['eval_loss']:.6f}")
            print(f"  MAE: " + " ".join(f"{v:.3f}" for v in metrics["mae_per_joint"].values()))
        except Exception as e:
            print(f"  ERROR during eval: {e}")
            import traceback; traceback.print_exc()
            results.append({"checkpoint": ckpt_path, "error": str(e)})
        finally:
            # Free GPU memory before loading next checkpoint
            del policy
            torch.cuda.empty_cache()

    # Rank by eval_loss
    valid = [r for r in results if "eval_loss" in r]
    valid.sort(key=lambda r: r["eval_loss"])
    all_ranked = valid + [r for r in results if "error" in r]

    output_path = args.output or str(Path.cwd() / "eval_ranking.json")
    with open(output_path, "w") as f:
        json.dump(all_ranked, f, indent=2)
    print(f"\nRanking saved to {output_path}")

    # Print summary
    print("\n=== RANKING ===")
    for i, r in enumerate(all_ranked):
        if "error" in r:
            print(f"  {i+1}. {Path(r['checkpoint']).name}: ERROR — {r['error']}")
        else:
            print(f"  {i+1}. {Path(r['checkpoint']).parent.parent.name}/{Path(r['checkpoint']).parent.name}")
            print(f"     loss={r['eval_loss']:.6f}  "
                  f"MAE_shld={r['mae_per_joint']['shoulder_pan']:.3f} "
                  f"MAE_elb={r['mae_per_joint']['elbow_flex']:.3f} "
                  f"MAE_wrst={r['mae_per_joint']['wrist_flex']:.3f}")

    # Success criteria
    best = valid[0] if valid else None
    if best:
        mae = best["mae_per_joint"]
        shoulder_ok = mae["shoulder_pan"] < 5.0 and mae["shoulder_lift"] < 5.0
        elbow_ok = mae["elbow_flex"] < 5.0
        wrist_ok = mae["wrist_flex"] < 2.0 and mae["wrist_roll"] < 2.0
        loss_ok = best["eval_loss"] < 0.10
        print(f"\n=== SUCCESS CRITERIA ===")
        print(f"  eval_loss < 0.10: {'PASS' if loss_ok else 'FAIL'} ({best['eval_loss']:.6f})")
        print(f"  shoulder MAE < 5°: {'PASS' if shoulder_ok else 'FAIL'}")
        print(f"  elbow MAE < 5°: {'PASS' if elbow_ok else 'FAIL'}")
        print(f"  wrist MAE < 2°: {'PASS' if wrist_ok else 'FAIL'}")
        if loss_ok and shoulder_ok and elbow_ok and wrist_ok:
            print("  OVERALL: PASS — ready for deployment")
        else:
            print("  OVERALL: NEEDS WORK — check worst joint")


if __name__ == "__main__":
    main()
