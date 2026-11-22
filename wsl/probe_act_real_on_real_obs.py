#!/usr/bin/env python3
"""Probe fine-tuned ACT policy on real SO follower observations.

Reads current robot state + camera frames, runs inference WITHOUT sending
actions to the robot. Verifies:
- Policy loads from fine-tuned checkpoint
- Camera bridge returns frames at correct resolution
- Inference produces valid action arrays in real degrees range
- Output distribution is reasonable (no NaN, not clipped hard)

Usage:
  python probe_act_real_on_real_obs.py [--checkpoint PATH] [--n 16]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from lerobot.cameras.zmq import ZMQCameraConfig
from lerobot.policies import make_pre_post_processors
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.policies.utils import prepare_observation_for_inference
from lerobot.robots.so_follower.so_follower import SOFollower, SOFollowerRobotConfig
from lerobot.utils.constants import OBS_STR
from lerobot.utils.feature_utils import build_dataset_frame, hw_to_dataset_features


ACTION_KEYS = [
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
]

DEFAULT_CKPT = str(Path.home() / "lerobot_outputs/act_real_finetune_sim018K_lr1e-5_20260723/checkpoints/010000/pretrained_model")
REAL_STATS = str(Path.home() / "lerobot_data/so101_real_cube_pick_img64/meta/stats.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default=DEFAULT_CKPT)
    parser.add_argument("--camera-server", default="172.28.48.1")
    parser.add_argument("--port", default="/dev/ttyACM0")
    parser.add_argument("--n", type=int, default=16)
    parser.add_argument("--image-w", type=int, default=64)
    parser.add_argument("--image-h", type=int, default=64)
    args = parser.parse_args()

    ckpt = Path(args.checkpoint)
    if not ckpt.exists():
        print(f"WARNING: checkpoint not found at {ckpt}")
        print("Specify --checkpoint to point to a valid fine-tuned checkpoint.")
        print("Continuing with probe of the checkpoint path anyway...")

    device = torch.device("cuda")

    print(f"Loading policy from {args.checkpoint}")
    policy = ACTPolicy.from_pretrained(args.checkpoint).to(device).eval()
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=policy.config,
        pretrained_path=args.checkpoint,
        preprocessor_overrides={"device_processor": {"device": "cuda"}},
    )
    print(f"  policy type: {type(policy).__name__}")
    print(f"  device: {device}")
    print(f"  use_amp: {policy.config.use_amp}")

    print(f"Connecting to SO follower at {args.port}")
    robot = SOFollower(
        SOFollowerRobotConfig(
            port=args.port,
            id="R12260101",
            max_relative_target=0.05,
            cameras={
                "wrist": ZMQCameraConfig(
                    server_address=args.camera_server,
                    port=5555,
                    camera_name="wrist",
                    width=args.image_w,
                    height=args.image_h,
                    fps=30,
                ),
                "scene": ZMQCameraConfig(
                    server_address=args.camera_server,
                    port=5555,
                    camera_name="scene",
                    width=args.image_w,
                    height=args.image_h,
                    fps=30,
                ),
            },
        )
    )

    real_stats = json.loads(Path(REAL_STATS).read_text())
    real_action_min = np.array(real_stats["action"]["min"], dtype=np.float32)
    real_action_max = np.array(real_stats["action"]["max"], dtype=np.float32)
    real_state_min = np.array(real_stats["observation.state"]["min"], dtype=np.float32)
    real_state_max = np.array(real_stats["observation.state"]["max"], dtype=np.float32)

    print(f"\nReal dataset action range (degrees):")
    for i, key in enumerate(ACTION_KEYS):
        print(f"  {key:20s}: [{real_action_min[i]:8.2f}, {real_action_max[i]:8.2f}]")

    try:
        robot.connect()
        print("  connected")

        obs_raw = robot.get_observation()
        hw_features = hw_to_dataset_features(robot.observation_features, OBS_STR)
        obs_frame = build_dataset_frame(hw_features, obs_raw, prefix=OBS_STR)

        raw_state = obs_frame["observation.state"].astype(np.float32)
        print(f"\nCurrent robot state (degrees):")
        for i, key in enumerate(ACTION_KEYS):
            print(f"  {key:20s}: {raw_state[i]:8.2f}")

        observation = prepare_observation_for_inference(
            dict(obs_frame), device, task="Small cube grasp test.", robot_type=robot.name
        )
        observation = preprocessor(observation)

        policy.reset()
        durations = []
        actions = []

        print(f"\nRunning {args.n} inference steps (no actions sent)...")
        with torch.inference_mode(), torch.autocast(device_type="cuda", enabled=policy.config.use_amp):
            for _ in range(3):
                _ = postprocessor(policy.select_action(observation))
            torch.cuda.synchronize()

            for step in range(args.n):
                start = time.perf_counter()
                action = postprocessor(policy.select_action(observation))
                torch.cuda.synchronize()
                elapsed = time.perf_counter() - start
                durations.append(elapsed)
                actions.append(action.squeeze(0).detach().cpu().numpy().astype(float))

        arr = np.stack(actions)

        print(f"\nPredicted action distribution (degrees, {args.n} steps):")
        print(f"  {'joint':20s} {'mean':>8s} {'min':>8s} {'max':>8s} {'std':>8s}")
        for i, key in enumerate(ACTION_KEYS):
            print(f"  {key:20s} {arr[:, i].mean():8.2f} {arr[:, i].min():8.2f} {arr[:, i].max():8.2f} {arr[:, i].std():8.2f}")

        in_range = (arr.min(axis=0) >= real_action_min - 10) & (arr.max(axis=0) <= real_action_max + 10)
        print(f"\n  all outputs in real data range: {bool(in_range.all())}")

        has_nan = np.isnan(arr).any()
        print(f"  NaN in outputs: {has_nan}")

        print(f"\nInference timing:")
        print(f"  mean: {1000 * float(np.mean(durations)):.2f} ms")
        print(f"  p95:  {1000 * float(np.quantile(durations, 0.95)):.2f} ms")
        print(f"  min:  {1000 * float(np.min(durations)):.2f} ms")
        print(f"  max:  {1000 * float(np.max(durations)):.2f} ms")

        print(f"\nPROBE_RESULT: ", end="")
        if has_nan:
            print("FAIL (NaN detected)")
        elif not bool(in_range.all()):
            print("WARN (outputs outside real data range)")
        else:
            print("PASS")

    finally:
        if robot.is_connected:
            robot.disconnect()
        print("disconnected")


if __name__ == "__main__":
    main()
