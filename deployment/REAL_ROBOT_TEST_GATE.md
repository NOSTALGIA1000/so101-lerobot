# SO-101 Real-Robot Test Gate

Date: 2026-07-22

## Current Status

The simulation pipeline has a working state-based chunked BC baseline:

```text
policy: training/outputs/chunk_bc_bootstrap_20_c10.npz
dataset: simulation/outputs/expert_dataset_bootstrap_20
eval episodes: 20
success_rate: 0.60
```

The policy is not yet a camera-observation policy. It uses:

```text
observation.state + cube_position + phase -> action chunk
```

So it is a sim benchmark/control baseline, not a deployable perception policy.

## Safety Dry-Run

The current dry-run script is:

```text
deployment/sim2real_safety.py
```

Validated output:

```text
deployment/outputs/sim2real_dry_run_chunk_bc_20.json
```

It checks:

- action dimension = 6
- SO-101 joint limit clipping
- conservative per-step action rate limiting
- policy metadata compatibility

It does not connect to hardware.

## Go / No-Go

### Allowed Today

- Run simulator evaluation.
- Run policy output dry-run.
- Run real robot read-only checks.
- Run low-speed no-cube joint-space playback only after follower read-only check passes.

### Not Recommended Yet

- Closed-loop cube grasp on the real robot.
- Any autonomous policy rollout near objects.
- Any test without physical emergency stop access.

## Required Before Cube-on-Table Real Test

1. State-based chunked policy reaches at least 80% simulation success on 50-100 randomized episodes.
2. Camera-observation dataset path is available.
3. Real robot joint readback matches simulation joint order:

   ```text
   shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper
   ```

4. Action units and signs are validated with low-speed single-joint moves.
5. Workspace bounds are enforced in the deployment wrapper.
6. Gripper open/close limits are tested without cube.

## Time Estimate From Current State

With 150 minutes remaining today:

- 20-40 min: more simulation policy debugging
- 20-30 min: dry-run and safety wrapper checks
- 20-40 min: follower read-only / low-speed no-cube checks if WSL USB is healthy
- 40-80 min: image/ACT path preparation, not full reliable training

Real cube grasp today is possible only as a manually supervised engineering
experiment, not as a validated policy deployment.
