# SO101 AutoDL ACT Training Runbook

Date: 2026-07-28

Scope: prepare the AutoDL/SeetaCloud training workflow for SO-ARM101 real-demo ACT training. The cloud instance is currently powered off, so this package is staged for the next power-on.

## First Priority: Use the AutoDL LeRobot Image Environment

If the instance was created from a LeRobot community image, use the image's native `lerobot` environment first.

Do not immediately clone latest upstream LeRobot or create `lerobot312`.

First check:

```bash
conda info --envs
conda activate lerobot
python -V
which lerobot-train
python -c "import lerobot; print(lerobot.__file__)"
pip show lerobot
```

Only create a new environment if the native image environment is proven unusable. If a new environment is required, create it on the data disk:

```bash
conda create -p /root/autodl-tmp/envs/lerobot312 python=3.12 -y
conda activate /root/autodl-tmp/envs/lerobot312
```

Set large caches to the data disk:

```bash
export HF_HOME=/root/autodl-tmp/huggingface
export PIP_CACHE_DIR=/root/autodl-tmp/pip-cache
export TORCH_HOME=/root/autodl-tmp/torch-cache
```

See also:

- `C:\Users\ASUS\Documents\lerobot\MEMORY_AUTODL_LEROBOT_ENV_20260728.md`

## Current Decision

Train order:

1. V2 first: `RItcheOhe/so101_cube_pick_place_v2`
2. Merge V3+V6 into `RItcheOhe/so101_cube_white_paper_v3v6`
3. Train V3V6
4. Train V4/V5 only after V2 and V3V6 have useful rollout candidates

Do not train:

- V1: old data
- V3 alone: already trained, drift observed, insufficient data alone

## Local vs AutoDL

Local RTX 4060 Laptop 8GB:

- Good for V3/V6/V4/V5 smoke tests at batch 8-16
- Good for dataset inspection and rollout preparation
- Not ideal for full V2 20k-step training because it occupies the local GPU for too long

AutoDL RTX 4090:

- Best for V2 formal training
- Best for V3V6 formal training
- Can also train V4/V5 later

## Prepared Files

Windows side:

- `C:\tmp\autodl_so101_setup_env.sh`
- `C:\tmp\autodl_train_v2.sh`
- `C:\tmp\autodl_merge_v3v6.sh`
- `C:\tmp\autodl_train_v3v6.sh`
- `C:\tmp\autodl_train_v4.sh`
- `C:\tmp\autodl_train_v5.sh`
- `C:\tmp\autodl_train_uploaded_v2.sh`
- `C:\tmp\autodl_train_uploaded_v7.sh`
- `C:\tmp\autodl_monitor.sh`
- `C:\tmp\autodl_package_ckpt.sh`
- `C:\tmp\autodl_upload_scripts.ps1`
- `C:\tmp\autodl_download_ckpt.ps1`

Project copy:

- `C:\Users\ASUS\Documents\lerobot\F-CCproject\codex-project\autodl-act\`

## Cloud Login

SSH endpoint from the current AutoDL page:

```powershell
ssh -p 45311 root@connect.bjb1.seetacloud.com
```

Do not store the password in scripts. Enter it interactively when SSH/SCP asks.

## First Power-On Procedure

From Windows PowerShell:

```powershell
cd C:\tmp
.\autodl_upload_scripts.ps1 -Port 45311 -HostName connect.bjb1.seetacloud.com
```

Then SSH into the cloud instance:

```powershell
ssh -p 45311 root@connect.bjb1.seetacloud.com
```

On the cloud instance:

```bash
bash /root/so101_autodl/autodl_so101_setup_env.sh
```

Then train V2:

```bash
nohup bash /root/so101_autodl/autodl_train_v2.sh > /root/autodl-tmp/so101_v2_train.nohup.log 2>&1 &
```

Monitor:

```bash
bash /root/so101_autodl/autodl_monitor.sh
tail -f /root/autodl-tmp/lerobot_outputs/act_cube_place_v2/train.log
```

## FileZilla Dataset Upload Mode

If V2 and V7 are uploaded manually with FileZilla, upload these local folders:

- `C:\Users\ASUS\Documents\lerobot\datasets\so101_cube_pick_place_v2`
- `C:\Users\ASUS\Documents\lerobot\datasets\so101_cube_white_paper_v7`

to this remote folder:

- `/root/autodl-tmp/huggingface/lerobot/`

Expected remote roots:

- `/root/autodl-tmp/huggingface/lerobot/so101_cube_pick_place_v2`
- `/root/autodl-tmp/huggingface/lerobot/so101_cube_white_paper_v7`

Training defaults for uploaded ACT datasets:

- `batch_size=32`
- `steps=100000`
- `save_freq=10000`

Then run:

```bash
nohup bash /root/so101_autodl/autodl_train_uploaded_v2.sh > /root/autodl-tmp/so101_uploaded_v2.nohup.log 2>&1 &
nohup bash /root/so101_autodl/autodl_train_uploaded_v7.sh > /root/autodl-tmp/so101_uploaded_v7.nohup.log 2>&1 &
```

## V3+V6

After V2 is running or completed, merge V3+V6:

```bash
bash /root/so101_autodl/autodl_merge_v3v6.sh
```

Then train:

```bash
nohup bash /root/so101_autodl/autodl_train_v3v6.sh > /root/autodl-tmp/so101_v3v6_train.nohup.log 2>&1 &
```

## Checkpoint Return

Package checkpoint on cloud:

```bash
bash /root/so101_autodl/autodl_package_ckpt.sh v2
bash /root/so101_autodl/autodl_package_ckpt.sh v3v6
```

Download from Windows:

```powershell
cd C:\tmp
.\autodl_download_ckpt.ps1 -Port 45311 -HostName connect.bjb1.seetacloud.com -RunName v2
.\autodl_download_ckpt.ps1 -Port 45311 -HostName connect.bjb1.seetacloud.com -RunName v3v6
```

## Success Criteria

V2 is ready for local rollout prep when:

- `checkpoints/100000/pretrained_model` exists, or the best intermediate checkpoint exists
- training log has no OOM, NaN, dataloader crash, or checkpoint write failure
- `config.json`, model weights, and dataset stats/config files are present in the checkpoint folder

V3V6 is ready when:

- merged repo is available as `RItcheOhe/so101_cube_white_paper_v3v6`
- training reaches a stable checkpoint
- no feature mismatch appears during merge or training

## Known Risks

- V3+V6 merge can fail if dataset features differ. Official LeRobot docs state merge requires identical features.
- If AutoDL image already has incompatible LeRobot installed, use the repository install under `/root/lerobot_workspace/lerobot`.
- If RTX 4090 still OOMs at batch 32, reduce to 16 first, then reduce workers from 8 to 4.
- Do not reuse old rollout scripts with `/mnt/c/Users/ASUS/~/...` paths; that path is invalid.
