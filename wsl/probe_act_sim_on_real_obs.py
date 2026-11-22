#!/usr/bin/env python3
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--checkpoint",
        default="/home/nostalgia/lerobot_outputs/act_sim_cube_until_2130/checkpoints/004000/pretrained_model",
    )
    parser.add_argument("--camera-server", default="172.28.48.1")
    parser.add_argument("--port", default="/dev/ttyACM0")
    parser.add_argument("--n", type=int, default=8)
    args = parser.parse_args()

    device = torch.device("cuda")
    ckpt = Path(args.checkpoint)
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
            max_relative_target=0.05,
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

    stats = json.load(open("/home/nostalgia/lerobot_data/so101_sim_cube_pick_img64/meta/stats.json"))
    sim_state_min = np.array(stats["observation.state"]["min"], dtype=np.float32)
    sim_state_max = np.array(stats["observation.state"]["max"], dtype=np.float32)
    sim_action_min = np.array(stats["action"]["min"], dtype=np.float32)
    sim_action_max = np.array(stats["action"]["max"], dtype=np.float32)

    try:
        robot.connect()
        obs_raw = robot.get_observation()
        hw_features = hw_to_dataset_features(robot.observation_features, OBS_STR)
        obs_frame = build_dataset_frame(hw_features, obs_raw, prefix=OBS_STR)

        raw_state = obs_frame["observation.state"].astype(np.float32)
        print("real_state_deg_order", ACTION_KEYS)
        print("real_state_deg", raw_state.tolist())
        print("sim_state_min_rad", sim_state_min.tolist())
        print("sim_state_max_rad", sim_state_max.tolist())
        print("real_state_vs_sim_range_ratio", ((raw_state - sim_state_min) / (sim_state_max - sim_state_min)).tolist())

        observation = prepare_observation_for_inference(
            dict(obs_frame), device, task="Small cube grasp test.", robot_type=robot.name
        )
        observation = preprocessor(observation)

        policy.reset()
        durations = []
        actions = []
        with torch.inference_mode(), torch.autocast(device_type="cuda", enabled=policy.config.use_amp):
            for _ in range(3):
                _ = postprocessor(policy.select_action(observation))
            torch.cuda.synchronize()
            for _ in range(args.n):
                start = time.perf_counter()
                action = postprocessor(policy.select_action(observation))
                torch.cuda.synchronize()
                durations.append(time.perf_counter() - start)
                actions.append(action.squeeze(0).detach().cpu().numpy().astype(float))

        arr = np.stack(actions)
        print("sim_action_min_rad", sim_action_min.tolist())
        print("sim_action_max_rad", sim_action_max.tolist())
        print("pred_action_mean", arr.mean(axis=0).tolist())
        print("pred_action_min", arr.min(axis=0).tolist())
        print("pred_action_max", arr.max(axis=0).tolist())
        print("inference_ms_mean", 1000 * float(np.mean(durations)))
        print("inference_ms_p95", 1000 * float(np.quantile(durations, 0.95)))
    finally:
        if robot.is_connected:
            robot.disconnect()


if __name__ == "__main__":
    main()
