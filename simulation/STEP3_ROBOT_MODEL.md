# Step 3: SO-101 Robot Model

Date: 2026-07-22

## Assets

Downloaded from `hf://buckets/lerobot/robot-urdfs`:

- `simulation/assets/robots/so101/so101_new_calib.urdf`
- `simulation/assets/robots/so101/so101_new_calib.mjcf.xml`
- `simulation/assets/robots/so101/so100.urdf`
- `simulation/assets/robots/so101/assets/*.stl`

The selected source model for the first benchmark is `so101_new_calib.urdf`.
For MuJoCo world inclusion, the URDF was compiled once into
`so101_new_calib.mjcf.xml`.

## Joint Order

The simulation joint order must match the local LeRobot real dataset:

1. `shoulder_pan`
2. `shoulder_lift`
3. `elbow_flex`
4. `wrist_flex`
5. `wrist_roll`
6. `gripper`

This is a 6D action/state layout. The gripper is the sixth action channel, not a separate seventh channel.

## Frames

- Base link: `base_link`
- End-effector frame: `gripper_frame_link`

`gripper_frame_link` should be used as the first IK target frame for expert demonstration generation.

## Files Added

- `simulation/robots/soarm101.py`
- `simulation/configs/robot.yaml`
- `simulation/robots/__init__.py`

## Next Step

Step 4 should create the MuJoCo cube-pick environment scaffold:

- tabletop world
- SO-101 robot loaded from the local asset
- cube randomized at reset
- RGB cameras named to match the real dataset where possible
- joint-position action interface
- observation dictionary compatible with LeRobot conversion
