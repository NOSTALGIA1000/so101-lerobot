# Current Status

Date: 2026-07-23

## Completed

- WSL is usable through the `LeRobot-Ubuntu-F` distro.
- Hugging Face / LeRobot environment runs in the WSL `lerobot` conda env.
- SO-ARM101 follower can be attached through `usbipd` and read through `/dev/ttyACM0`.
- Windows camera bridge can stream `wrist` and `scene` cameras to WSL.
- Simulation cube-pick environment and synthetic dataset pipeline exist.
- LeRobot v3 sim dataset exists and validates.
- ACT smoke training has produced usable checkpoints.
- Real robot deployment chain has been tested with bounded reach/grip demos.
- Sim2real adapter exists for unit conversion and local action limiting.

## Important Finding

The current sim ACT checkpoint is not a real grasp policy.

It is useful for validating the deployment path, but it does not solve:

```text
real image domain gap
real robot action/state distribution
cube contact dynamics
```

## Latest Known Good Sim ACT Checkpoint

```text
/home/nostalgia/lerobot_outputs/act_sim_cube_until_2130/checkpoints/004000/pretrained_model
```

## New Optimized Training Run

Training script:

```text
wsl/train_act_sim_optimized.sh
```

Default output:

```text
/home/nostalgia/lerobot_outputs/act_sim_cube_optimized_20260723
```

Default log when launched by Codex:

```text
/mnt/c/Users/ASUS/Documents/lerobot/wsl/act_sim_cube_optimized_20260723.log
```

## Real-Robot Safety State

Before the next hardware test:

1. Confirm SO-ARM101 power is on.
2. Confirm CH343 is visible and attached to WSL.
3. Run `wsl/check_follower_readonly.py`.
4. Run camera bridge check.
5. Run policy dry-run/probe before sending actions.

## Real-Demo Data Audit (2026-07-23)

Real demonstration dataset found at `datasets/so101_grasp_cube_test_20260721_200217/`.

**Key finding: data already in LeRobot v3.0 format.** No raw conversion needed.

- 46 episodes, 19,958 frames, 30 FPS
- State/action: real SO follower **degrees** (NOT MuJoCo radians)
- Images: 640×480, AV1 codec, dual camera (scene + wrist)
- Robot type: `so_follower` (not `so101` sim)

See: `F-CCproject/codex-project/REAL_DEMO_DATA_AUDIT_20260723.md`

## Real-Demo Fine-Tune Plan (2026-07-23)

Resolution adaptation needed: sim checkpoint uses 64×64, real data is 640×480.
Plan: downsample real data to 64×64 → fine-tune ACT from sim checkpoint.

New scripts created:

```text
wsl/create_real_dataset_64x64.py    # 640x480 -> 64x64 LeRobot v3 dataset
wsl/train_act_real_finetune.sh      # Fine-tune ACT from sim ckpt on real 64x64
wsl/probe_act_real_on_real_obs.py   # Dry-run inference probe
wsl/rollout_act_real_nocube.sh      # Safe no-cube reach/grip test
wsl/rollout_act_real_cube.sh        # Cube contact test
```

See: `F-CCproject/codex-project/REAL_TO_LEROBOT_CONVERSION_PLAN_20260723.md`

## ACT Real-Data Fine-Tune Results (2026-07-23)

Training completed: 10,000 steps in ~12 min.

| Metric | Start (step 50) | End (step 10K) |
|--------|-----------------|-----------------|
| Train loss | 1.831 | 0.332 |
| Eval loss | 0.633 (step 500) | 0.534 (step 10K) |
| L1 loss | 0.695 | 0.233 |
| KLD loss | 0.114 | 0.010 |

Loss trajectory: steady decline, no overfitting. Best eval: 0.534 at step 10K.

Checkpoints: 001000–010000 at:
```
/home/nostalgia/lerobot_outputs/act_real_finetune_20260723/checkpoints/
```

Latest known good: `checkpoints/010000/pretrained_model`

## Next Step

1. ~~`python wsl/create_real_dataset_64x64.py`~~ — DONE
2. ~~`bash wsl/train_act_real_finetune.sh`~~ — DONE (10K steps, eval_loss=0.534)
3. `python wsl/probe_act_real_on_real_obs.py` — verify inference (NEXT)
4. `bash wsl/rollout_act_real_nocube.sh` — hardware safety test
5. `bash wsl/rollout_act_real_cube.sh` — cube contact test
