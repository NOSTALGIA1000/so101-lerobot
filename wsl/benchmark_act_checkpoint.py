#!/usr/bin/env python
import argparse
import time

import torch

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies import make_pre_post_processors
from lerobot.policies.act.modeling_act import ACTPolicy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint")
    parser.add_argument(
        "--dataset-root",
        default="/home/nostalgia/lerobot_data/so101_grasp_cube_test_20260721_200217",
    )
    args = parser.parse_args()

    device = torch.device("cuda")
    dataset = LeRobotDataset(
        repo_id="local/so101_grasp_cube_test_20260721_200217",
        root=args.dataset_root,
    )
    policy = ACTPolicy.from_pretrained(args.checkpoint).to(device).eval()
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=policy.config,
        pretrained_path=args.checkpoint,
        preprocessor_overrides={"device_processor": {"device": "cuda"}},
    )

    sample = dataset[0]
    required = set(policy.config.input_features)
    observation = {
        key: value.unsqueeze(0)
        for key, value in sample.items()
        if key in required and isinstance(value, torch.Tensor)
    }
    missing = required - set(observation)
    if missing:
        raise RuntimeError(f"Missing policy inputs: {sorted(missing)}")

    observation = preprocessor(observation)
    print(f"required_inputs={sorted(required)}")
    print(f"loaded_inputs={sorted(observation)}")

    with torch.inference_mode(), torch.autocast(device_type="cuda", enabled=policy.config.use_amp):
        for _ in range(3):
            policy.reset()
            action = postprocessor(policy.select_action(observation))
        torch.cuda.synchronize()

        durations = []
        for _ in range(20):
            policy.reset()  # Force a new ACT chunk inference each measurement.
            start = time.perf_counter()
            action = postprocessor(policy.select_action(observation))
            torch.cuda.synchronize()
            durations.append(time.perf_counter() - start)

    mean_s = sum(durations) / len(durations)
    p95_s = sorted(durations)[int(len(durations) * 0.95) - 1]
    print(f"action_shape={tuple(action.shape)}")
    print(f"mean_inference_ms={mean_s * 1000:.2f}")
    print(f"p95_inference_ms={p95_s * 1000:.2f}")
    print(f"mean_inference_hz={1 / mean_s:.2f}")


if __name__ == "__main__":
    main()
