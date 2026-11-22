# Step 6: Behavior Cloning Baseline

Date: 2026-07-22

## Status

Implemented and trained a lightweight NumPy behavior cloning baseline. The
baseline is useful for validating dataset/action alignment, but it is not yet a
robust closed-loop controller.

## Files

- `training/train_bc.py`
- `training/README_SIM_TRAINING.md`
- `training/outputs/bc_state_cube_policy.npz`
- `training/outputs/bc_state_cube_policy_50ep.npz`
- `training/outputs/bc_state_cube_phase_policy_50ep.npz`

## Model Inputs

The latest baseline trains:

```text
observation.state + cube_position + phase -> action
```

This is a state-based debugging baseline, not the final camera-observation policy.

## Training Result

Using `simulation/outputs/expert_dataset_50`:

```text
steps: 3000
final val_loss: 0.001093
```

The model fits the assisted expert actions numerically.

## Important Limitation

Rollout success remains sensitive to dataset representation. A scalar phase
BC model can fit expert actions with low validation loss, but closed-loop
execution averages across different cube poses and task phases.

The current best debugging checkpoint is:

```text
training/outputs/chunk_bc_bootstrap_20_c10.npz
```

Training:

```text
dataset: simulation/outputs/expert_dataset_bootstrap_20
episodes: 20
frames: 8400
policy: chunked BC
chunk_size: 10
hidden_dim: 512
steps: 2000
final val_loss: 0.000046
```

Evaluation:

```text
episodes: 20
max_steps: 420
execute_chunk: 10
success_rate: 0.60
mean_max_cube_height: 0.0830 m
```

The scalar-action BC baseline reached only 0.25 success under the same setting.
Chunked action prediction is a better match for this scripted manipulation task
and is the correct bridge toward full ACT.

## Rejected Follow-up Experiments

These checkpoints should not be used for deployment:

- `training/outputs/chunk_bc_bootstrap_50_c10_h512_s3000.npz`
  - 30-episode eval success: 0.30
  - failure mode: broader 50-episode distribution degraded closed-loop behavior.
- `training/outputs/chunk_bc_bootstrap_50_c10_h512_lr3e4_s3000.npz`
  - 30-episode eval success: 0.033
  - failure mode: lower learning rate improved validation loss but not rollout.
- `training/outputs/chunk_bc_bootstrap_20_ee_c10_h512_s2000.npz`
  - 20-episode eval success: 0.0
  - failure mode: adding `ee_position` lowered validation loss but created rollout
    distribution mismatch in the current simulator.

The active policy registry is:

```text
deployment/policy_registry.json
```

## Next Required Fix

Improve physical grasping before scaling training:

- tune gripper geometry/contact
- add opposing jaw/contact surface if needed
- tune cube friction/mass
- make expert succeed without `grasp_assist`
- only then export full LeRobot parquet/video data

For policy learning, the next practical step is to move from scalar-phase BC to
chunked action prediction, matching the intended ACT training setup.
