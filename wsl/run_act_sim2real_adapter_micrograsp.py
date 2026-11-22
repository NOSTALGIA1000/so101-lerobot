#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import torch

from lerobot.cameras.zmq import ZMQCameraConfig
from lerobot.policies import make_pre_post_processors
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.policies.utils import prepare_observation_for_inference
from lerobot.robots.so_follower.so_follower import SOFollower, SOFollowerRobotConfig


ACTION_KEYS = [
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
]


def clamp_step(current: float, target: float, max_delta: float) -> float:
    delta = max(-max_delta, min(max_delta, target - current))
    return current + delta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--checkpoint",
        default="/home/nostalgia/lerobot_outputs/act_sim_cube_until_2130/checkpoints/004000/pretrained_model",
    )
    parser.add_argument("--camera-server", default="172.28.48.1")
    parser.add_argument("--port", default="/dev/ttyACM0")
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--fps", type=float, default=10.0)
    parser.add_argument("--max-step-deg", type=float, default=0.35)
    parser.add_argument("--max-step-gripper", type=float, default=0.8)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--return-home", action="store_true")
    args = parser.parse_args()

    stats = json.load(open("/home/nostalgia/lerobot_data/so101_sim_cube_pick_img64/meta/stats.json"))
    sim_grip_min = float(stats["action"]["min"][5])
    sim_grip_max = float(stats["action"]["max"][5])

    device = torch.device("cuda")
    policy = ACTPolicy.from_pretrained(args.checkpoint).to(device).eval()
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=policy.config,
        pretrained_path=args.checkpoint,
        preprocessor_overrides={"device_processor": {"device": "cuda"}},
    )

    robot = SOFollower(
        SOFollowerRobotConfig(
            port=args.port,
            id="R12260101",
            # Keep LeRobot's own guard active as a final safety layer.
            max_relative_target=max(args.max_step_deg, args.max_step_gripper),
            cameras={
                "wrist": ZMQCameraConfig(
                    server_address=args.camera_server,
                    port=5555,
                    camera_name="wrist",
                    width=64,
                    height=64,
                    fps=30,
                ),
                "scene": ZMQCameraConfig(
                    server_address=args.camera_server,
                    port=5555,
                    camera_name="scene",
                    width=64,
                    height=64,
                    fps=30,
                ),
            },
        )
    )

    def real_obs_to_policy_obs(obs_raw: dict) -> dict:
        real = np.array([float(obs_raw[k]) for k in ACTION_KEYS], dtype=np.float32)
        state = real.copy()
        state[:5] = np.deg2rad(state[:5])
        # SO follower gripper is normalized 0..100; sim gripper is radians.
        state[5] = sim_grip_min + (np.clip(real[5], 0, 100) / 100.0) * (sim_grip_max - sim_grip_min)
        return {
            "observation.state": state,
            "observation.images.wrist": obs_raw["wrist"],
            "observation.images.scene": obs_raw["scene"],
        }

    def sim_action_to_real_target(action: np.ndarray) -> dict[str, float]:
        # Sim first five joints are radians; real SO follower expects degrees.
        target = np.empty(6, dtype=np.float32)
        target[:5] = np.rad2deg(action[:5])
        # Map sim gripper radians back to SO follower 0..100.
        target[5] = 100.0 * (float(action[5]) - sim_grip_min) / (sim_grip_max - sim_grip_min)
        target[5] = float(np.clip(target[5], 0, 100))
        return {k: float(v) for k, v in zip(ACTION_KEYS, target)}

    def safe_target(current: dict[str, float], target: dict[str, float]) -> dict[str, float]:
        out = {}
        for k in ACTION_KEYS[:5]:
            out[k] = clamp_step(float(current[k]), float(target[k]), args.max_step_deg)
        out[ACTION_KEYS[5]] = clamp_step(
            float(current[ACTION_KEYS[5]]), float(target[ACTION_KEYS[5]]), args.max_step_gripper
        )
        return out

    try:
        robot.connect()
        initial = {k: float(v) for k, v in robot.get_observation().items() if k in ACTION_KEYS}
        policy.reset()
        period = 1.0 / args.fps
        deadline = time.perf_counter() + args.duration
        tick = 0
        last_safe = initial

        print("initial_real", initial)
        while time.perf_counter() < deadline:
            loop_start = time.perf_counter()
            obs_raw = robot.get_observation()
            current = {k: float(obs_raw[k]) for k in ACTION_KEYS}
            observation = prepare_observation_for_inference(
                real_obs_to_policy_obs(obs_raw),
                device,
                task="Small cube grasp test.",
                robot_type=robot.name,
            )
            observation = preprocessor(observation)
            with torch.inference_mode(), torch.autocast(device_type="cuda", enabled=policy.config.use_amp):
                action = postprocessor(policy.select_action(observation))
            sim_action = action.squeeze(0).detach().cpu().numpy().astype(np.float32)
            real_target = sim_action_to_real_target(sim_action)
            guarded = safe_target(current, real_target)
            if tick % max(int(args.fps), 1) == 0:
                print(
                    "tick",
                    tick,
                    "current",
                    {k: round(current[k], 3) for k in ACTION_KEYS},
                    "raw_target",
                    {k: round(real_target[k], 3) for k in ACTION_KEYS},
                    "guarded",
                    {k: round(guarded[k], 3) for k in ACTION_KEYS},
                )
            if not args.dry_run:
                robot.send_action(guarded)
            last_safe = guarded
            tick += 1
            sleep_s = period - (time.perf_counter() - loop_start)
            if sleep_s > 0:
                time.sleep(sleep_s)

        print("ticks", tick, "last_safe", last_safe)

        if args.return_home and not args.dry_run:
            steps = max(int(3 * args.fps), 1)
            obs_raw = robot.get_observation()
            current = {k: float(obs_raw[k]) for k in ACTION_KEYS}
            for i in range(steps):
                alpha = (i + 1) / steps
                target = {k: current[k] * (1 - alpha) + initial[k] * alpha for k in ACTION_KEYS}
                robot.send_action(target)
                time.sleep(period)
            print("returned_home", initial)
    finally:
        if robot.is_connected:
            robot.disconnect()


if __name__ == "__main__":
    main()
