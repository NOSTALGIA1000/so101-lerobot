# SO101 AutoDL Native LeRobot Flow

Date: 2026-07-28

This file is the preferred AutoDL workflow for the current SO101 datasets. It follows the tutorial style: use the AutoDL LeRobot image environment first, place datasets under `HF_HOME`, and train with `lerobot-train`.

## Current Uploaded Data

Expected cloud data roots:

```bash
/root/autodl-tmp/huggingface/lerobot/so101_cube_pick_place_v2
/root/autodl-tmp/huggingface/lerobot/so101_cube_white_paper_v7
```

Each dataset root must contain:

```text
data/
meta/
videos/
```

## First Rule

Use the AutoDL image's native environment first:

```bash
conda activate lerobot
```

Do not create a new environment unless this native environment is proven broken.

Do not install large PyTorch packages into the system disk unless disk space has been checked.

## Boot Checklist

Run this after each AutoDL boot:

```bash
df -h / /root/autodl-tmp
conda info --envs
conda activate lerobot
python -V
which lerobot-train
python -c "import lerobot; print(lerobot.__file__)"
```

Dataset check:

```bash
export HF_HOME=/root/autodl-tmp/huggingface
ls -lah /root/autodl-tmp/huggingface/lerobot
ls -lah /root/autodl-tmp/huggingface/lerobot/so101_cube_pick_place_v2
ls -lah /root/autodl-tmp/huggingface/lerobot/so101_cube_white_paper_v7
```

## Train V2

This follows the tutorial default ACT training style. ACT defaults are expected to use `batch_size=32` and `steps=100000`.

```bash
export HF_HOME=/root/autodl-tmp/huggingface
export WANDB_MODE=disabled
mkdir -p /root/autodl-tmp/lerobot_outputs

nohup lerobot-train \
  --dataset.repo_id=so101_cube_pick_place_v2 \
  --policy.type=act \
  --output_dir=/root/autodl-tmp/lerobot_outputs/act_so101_cube_pick_place_v2 \
  --job_name=act_so101_cube_pick_place_v2 \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --wandb.enable=false \
  > /root/autodl-tmp/act_so101_cube_pick_place_v2.log 2>&1 &
```

Monitor:

```bash
tail -f /root/autodl-tmp/act_so101_cube_pick_place_v2.log
nvidia-smi
```

If the native image cannot resolve the dataset from `HF_HOME`, rerun with an explicit dataset root:

```bash
nohup lerobot-train \
  --dataset.repo_id=so101_cube_pick_place_v2 \
  --dataset.root=/root/autodl-tmp/huggingface/lerobot/so101_cube_pick_place_v2 \
  --policy.type=act \
  --output_dir=/root/autodl-tmp/lerobot_outputs/act_so101_cube_pick_place_v2 \
  --job_name=act_so101_cube_pick_place_v2 \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --wandb.enable=false \
  > /root/autodl-tmp/act_so101_cube_pick_place_v2.log 2>&1 &
```

## Train V7

Run after V2 has at least produced usable checkpoints.

```bash
export HF_HOME=/root/autodl-tmp/huggingface
export WANDB_MODE=disabled
mkdir -p /root/autodl-tmp/lerobot_outputs

nohup lerobot-train \
  --dataset.repo_id=so101_cube_white_paper_v7 \
  --policy.type=act \
  --output_dir=/root/autodl-tmp/lerobot_outputs/act_so101_cube_white_paper_v7 \
  --job_name=act_so101_cube_white_paper_v7 \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --wandb.enable=false \
  > /root/autodl-tmp/act_so101_cube_white_paper_v7.log 2>&1 &
```

If dataset lookup fails:

```bash
nohup lerobot-train \
  --dataset.repo_id=so101_cube_white_paper_v7 \
  --dataset.root=/root/autodl-tmp/huggingface/lerobot/so101_cube_white_paper_v7 \
  --policy.type=act \
  --output_dir=/root/autodl-tmp/lerobot_outputs/act_so101_cube_white_paper_v7 \
  --job_name=act_so101_cube_white_paper_v7 \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --wandb.enable=false \
  > /root/autodl-tmp/act_so101_cube_white_paper_v7.log 2>&1 &
```

## Package Checkpoint

After training:

```bash
mkdir -p /root/autodl-tmp/so101_ckpt_packages
LATEST=$(find /root/autodl-tmp/lerobot_outputs/act_so101_cube_pick_place_v2/checkpoints -maxdepth 2 -type d -name pretrained_model | sort | tail -1)
CKPT_DIR=$(dirname "$LATEST")
tar -C "$CKPT_DIR" -czf /root/autodl-tmp/so101_ckpt_packages/v2_$(basename "$CKPT_DIR")_pretrained_model.tar.gz pretrained_model
```

For V7:

```bash
LATEST=$(find /root/autodl-tmp/lerobot_outputs/act_so101_cube_white_paper_v7/checkpoints -maxdepth 2 -type d -name pretrained_model | sort | tail -1)
CKPT_DIR=$(dirname "$LATEST")
tar -C "$CKPT_DIR" -czf /root/autodl-tmp/so101_ckpt_packages/v7_$(basename "$CKPT_DIR")_pretrained_model.tar.gz pretrained_model
```

Download `/root/autodl-tmp/so101_ckpt_packages/*.tar.gz` with FileZilla.

## Do Not Repeat

Do not run `pip install -e .` inside:

```bash
/root/autodl-tmp/huggingface/lerobot
```

That is the dataset folder, not the code folder.

Only run `pip install -e .` inside an actual LeRobot source folder containing `pyproject.toml`, and only if the native image environment is confirmed incomplete.

