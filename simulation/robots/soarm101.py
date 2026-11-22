"""SO-101 / SO-ARM101 robot asset description.

This module intentionally stays simulator-light. The MuJoCo environment can use
it to locate assets and keep joint ordering aligned with the real LeRobot
dataset before we add task-specific logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class JointSpec:
    name: str
    lower: float
    upper: float
    effort: float = 10.0
    velocity: float = 10.0


@dataclass(frozen=True)
class SOArm101Spec:
    name: str
    urdf_path: Path
    mjcf_path: Path
    mesh_dir: Path
    base_link: str
    ee_link: str
    joint_specs: tuple[JointSpec, ...]
    state_keys: tuple[str, ...]
    action_keys: tuple[str, ...]

    @property
    def joint_names(self) -> tuple[str, ...]:
        return tuple(joint.name for joint in self.joint_specs)

    @property
    def action_dim(self) -> int:
        return len(self.action_keys)

    @property
    def state_dim(self) -> int:
        return len(self.state_keys)

    def validate_assets(self) -> None:
        if not self.urdf_path.exists():
            raise FileNotFoundError(f"URDF not found: {self.urdf_path}")
        if not self.mjcf_path.exists():
            raise FileNotFoundError(f"MJCF not found: {self.mjcf_path}")
        if not self.mesh_dir.exists():
            raise FileNotFoundError(f"Mesh directory not found: {self.mesh_dir}")


SOARM101 = SOArm101Spec(
    name="so101_new_calib",
    urdf_path=REPO_ROOT / "simulation" / "assets" / "robots" / "so101" / "so101_new_calib.urdf",
    mjcf_path=REPO_ROOT / "simulation" / "assets" / "robots" / "so101" / "so101_new_calib.mjcf.xml",
    mesh_dir=REPO_ROOT / "simulation" / "assets" / "robots" / "so101" / "assets",
    base_link="base_link",
    ee_link="gripper_frame_link",
    joint_specs=(
        JointSpec("shoulder_pan", -1.91986, 1.91986),
        JointSpec("shoulder_lift", -1.74533, 1.74533),
        JointSpec("elbow_flex", -1.69, 1.69),
        JointSpec("wrist_flex", -1.65806, 1.65806),
        JointSpec("wrist_roll", -2.74385, 2.84121),
        JointSpec("gripper", -0.174533, 1.74533),
    ),
    state_keys=(
        "shoulder_pan.pos",
        "shoulder_lift.pos",
        "elbow_flex.pos",
        "wrist_flex.pos",
        "wrist_roll.pos",
        "gripper.pos",
    ),
    action_keys=(
        "shoulder_pan.pos",
        "shoulder_lift.pos",
        "elbow_flex.pos",
        "wrist_flex.pos",
        "wrist_roll.pos",
        "gripper.pos",
    ),
)


def get_robot_spec() -> SOArm101Spec:
    SOARM101.validate_assets()
    return SOARM101
