# Full Chain Workflow

## Objective

Train and evaluate a policy for:

```text
SO-ARM101 + Cube Pick
observation -> action
```

The long-term target is a real robot cube grasp. The current working path is:

```text
simulation data -> ACT training -> simulation evaluation -> safe real rollout -> real-demo alignment -> ACT fine-tuning -> real grasp
```

## Current Pipeline

### 1. Simulation Environment

```text
simulation/environments/soarm101_cube_pick_env.py
simulation/robots/soarm101.py
simulation/configs/robot.yaml
simulation/configs/task.yaml
```

Simulation task:

```text
approach cube -> align gripper -> grasp -> lift -> move/place
```

Current action/state dimension:

```text
6 = five arm joints + gripper
```

### 2. Simulation Dataset

Compact synthetic dataset was generated first, then converted to LeRobot v3.

LeRobot dataset:

```text
/home/nostalgia/lerobot_data/so101_sim_cube_pick_img64
repo_id: local/so101_sim_cube_pick_img64
```

Converter:

```text
wsl/convert_act_smoke_npz_to_lerobot_v3.py
```

### 3. ACT Simulation Training

Primary training command:

```text
wsl/train_act_sim_optimized.sh
```

Current optimized output path:

```text
/home/nostalgia/lerobot_outputs/act_sim_cube_optimized_20260723
```

Previous useful checkpoint:

```text
/home/nostalgia/lerobot_outputs/act_sim_cube_until_2130/checkpoints/004000/pretrained_model
```

### 4. Real-Robot Deployment Check

Required checks before any action:

```text
CH343 attached to WSL as /dev/ttyACM0
follower read-only check passes
camera bridge exposes wrist and scene streams
policy probe runs without sending actions
```

Read-only scripts:

```text
wsl/check_follower_readonly.py
wsl/check_camera_bridge.py
wsl/probe_act_sim_on_real_obs.py
```

### 5. Sim2Real Adapter

Direct sim ACT rollout is not semantically correct on the real robot.

Adapter:

```text
wsl/run_act_sim2real_adapter_micrograsp.py
```

The adapter converts:

```text
real arm degrees -> sim radians for policy input
sim radians -> real arm degrees for action output
real gripper scale <-> sim gripper range
```

It also applies per-step local action limits.

### 6. Current Real-Robot Result

The real robot can run bounded reach/grip demos.

It has not yet achieved reliable cube grasp.

Observed blocker:

```text
sim-only ACT does not know real camera appearance or real action distribution well enough
```

## Next Correct Step

Use real teleoperation demonstrations:

```text
real demos -> LeRobot dataset -> ACT fine-tune -> safe real evaluation
```

This is the path that can plausibly produce a real cube grasp.

## Real-Demo Fine-Tuning Plan

1. Locate real demonstration files.
2. Inspect one episode fully.
3. Define real dataset schema.
4. Convert to LeRobot v3.
5. Validate dataset stats and image/action alignment.
6. Fine-tune ACT from the best compatible checkpoint.
7. Run dry-run policy probe.
8. Run no-cube reach/grip.
9. Run cube contact test.
10. Attempt grasp/lift only after the previous steps pass.
