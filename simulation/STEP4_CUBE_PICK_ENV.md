# Step 4: Cube Pick Environment

Date: 2026-07-22

## Status

Created a minimal MuJoCo SO-101 cube-pick environment scaffold.

## Files Added

- `simulation/assets/worlds/so101_cube_pick.xml`
- `simulation/assets/cube/cube.xml`
- `simulation/configs/task.yaml`
- `simulation/environments/soarm101_cube_pick_env.py`
- `simulation/environments/__init__.py`

## Files Updated

- `simulation/assets/robots/so101/so101_new_calib.mjcf.xml`
  - Added a `wrist` camera under `gripper_link`.

## Environment Features

- Loads the local SO-101 MuJoCo model.
- Uses joint position control.
- Action dimension: 6.
- State dimension: 6.
- Includes a tabletop.
- Includes a free cube.
- Randomizes cube position, size, yaw, and color on reset.
- Renders two RGB cameras:
  - `observation.images.scene`
  - `observation.images.wrist`
- Returns LeRobot-style observation keys where practical.

## Smoke Test

The environment was validated with the project-local MuJoCo install:

```powershell
$env:PYTHONPATH='C:\Users\ASUS\Documents\lerobot;C:\Users\ASUS\Documents\lerobot\.sim_deps'
& 'C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  'C:\Users\ASUS\Documents\lerobot\simulation\environments\soarm101_cube_pick_env.py'
```

Observed output:

```text
state_shape: (6,)
image_shape: (480, 640, 3)
```

A follow-up check confirmed both `scene` and `wrist` render at `(480, 640, 3)`.

## Known Gaps

- No expert policy yet.
- No IK or motion planning yet.
- No LeRobot dataset writer yet.
- Reward and success condition are placeholders.
- Contact/gripper behavior still needs task-specific tuning.

## Next Step

Step 5 should implement simulation demonstration generation:

- IK target sequence:
  - pre-grasp
  - align
  - descend
  - close gripper
  - lift
  - place
- save observations/actions in a LeRobot-compatible layout
- start with a small dataset smoke test before generating many episodes
