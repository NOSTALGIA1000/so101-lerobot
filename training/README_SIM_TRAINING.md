# Simulation Training

This folder starts with a dependency-light behavior cloning baseline.

## BC Baseline

`train_bc.py` trains:

```text
observation.state + cube_position + phase -> action
```

It is not the final visual policy. It exists to validate the end-to-end
simulation data and training loop before moving to image-based BC, ACT, and
Diffusion Policy.

Default input dataset:

```text
simulation/outputs/expert_dataset_smoke_v4
```

Default output:

```text
training/outputs/bc_state_cube_policy.npz
```
