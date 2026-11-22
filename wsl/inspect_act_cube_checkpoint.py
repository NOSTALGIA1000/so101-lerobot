#!/usr/bin/env python3
import json
from pathlib import Path

ckpt = Path("/home/nostalgia/lerobot_outputs/act_cube_v1/checkpoints/020000")
cfg_path = ckpt / "pretrained_model" / "train_config.json"
cfg = json.loads(cfg_path.read_text())

for key in ["output_dir", "steps", "eval_freq", "save_freq", "log_freq", "resume", "pretrained_path", "checkpoint_path"]:
    print(f"{key}={cfg.get(key)!r}")

print("policy_pretrained_path=", cfg.get("policy", {}).get("pretrained_path"))
print("model_exists=", (ckpt / "pretrained_model" / "model.safetensors").exists())
print("root_model_exists=", (ckpt / "model.safetensors").exists())
print("training_state_exists=", (ckpt / "training_state").exists())
