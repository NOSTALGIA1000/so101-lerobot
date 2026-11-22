"""MuJoCo SO-101 cube-pick environment scaffold."""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DEPS = REPO_ROOT / ".sim_deps"
if SIM_DEPS.exists() and str(SIM_DEPS) not in sys.path:
    sys.path.insert(0, str(SIM_DEPS))

import mujoco  # noqa: E402

from simulation.robots.soarm101 import SOARM101


@dataclass(frozen=True)
class CubePickConfig:
    model_path: Path = REPO_ROOT / "simulation" / "assets" / "worlds" / "so101_cube_pick.xml"
    fps: int = 30
    image_width: int = 640
    image_height: int = 480
    cube_x_range: tuple[float, float] = (0.16, 0.30)
    cube_y_range: tuple[float, float] = (-0.12, 0.12)
    cube_size_range: tuple[float, float] = (0.025, 0.032)
    direct_joint_position_control: bool = True
    abstract_grasp: bool = True
    grasp_threshold: float = 0.18
    grasp_offset_z: float = 0.055
    closed_gripper_threshold: float = 0.15
    open_gripper_threshold: float = 1.0


class SOArm101CubePickEnv:
    """Minimal MuJoCo environment with LeRobot-style observations."""

    metadata = {"render_modes": ["rgb_array"]}

    def __init__(self, config: CubePickConfig | None = None, seed: int | None = None) -> None:
        self.config = config or CubePickConfig()
        self.rng = np.random.default_rng(seed)
        self.robot = SOARM101
        self.robot.validate_assets()

        self.model = mujoco.MjModel.from_xml_path(str(self.config.model_path))
        self.data = mujoco.MjData(self.model)
        self.control_dt = 1.0 / self.config.fps
        self.physics_steps_per_control = max(1, round(self.control_dt / self.model.opt.timestep))

        self.joint_ids = [self.model.joint(name).id for name in self.robot.joint_names]
        self.actuator_ids = [self.model.actuator(f"{name}_pos").id for name in self.robot.joint_names]
        self.cube_body_id = self.model.body("cube").id
        self.cube_geom_id = self.model.geom("cube_geom").id
        self.scene_camera_id = self.model.camera("scene").id
        self.wrist_camera_id = self.model.camera("wrist").id
        self.ee_site_id = self.model.site("ee_site").id
        self._grasped = False

        self.renderer = mujoco.Renderer(
            self.model,
            height=self.config.image_height,
            width=self.config.image_width,
        )
        self._step_count = 0

    def reset(self) -> dict[str, Any]:
        mujoco.mj_resetData(self.model, self.data)
        self._step_count = 0
        self._grasped = False
        self._randomize_cube()
        mujoco.mj_forward(self.model, self.data)
        return self._get_observation()

    def step(self, action: np.ndarray) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        action = np.asarray(action, dtype=np.float64)
        if action.shape != (self.robot.action_dim,):
            raise ValueError(f"Expected action shape {(self.robot.action_dim,)}, got {action.shape}")

        clipped = self._clip_action(action)
        for actuator_id, target in zip(self.actuator_ids, clipped):
            self.data.ctrl[actuator_id] = target

        for _ in range(self.physics_steps_per_control):
            if self.config.direct_joint_position_control:
                self._set_robot_qpos(clipped)
                self._update_abstract_grasp(clipped)
            mujoco.mj_step(self.model, self.data)
            self._update_abstract_grasp(clipped)

        self._step_count += 1
        obs = self._get_observation()
        reward = self._compute_reward(obs)
        terminated = bool(obs["state"]["cube_position"][2] > 0.08)
        truncated = False
        info = {"is_success": terminated}
        return obs, reward, terminated, truncated, info

    def render(self, camera: str = "scene") -> np.ndarray:
        self.renderer.update_scene(self.data, camera=camera)
        return self.renderer.render()

    def close(self) -> None:
        self.renderer.close()

    def _randomize_cube(self) -> None:
        size = self.rng.uniform(*self.config.cube_size_range)
        x = self.rng.uniform(*self.config.cube_x_range)
        y = self.rng.uniform(*self.config.cube_y_range)
        yaw = self.rng.uniform(-math.pi, math.pi)

        self.model.geom_size[self.cube_geom_id] = np.array([size, size, size])
        self.data.qpos[self._cube_qpos_slice()] = np.array(
            [x, y, size + 0.001, math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)]
        )

        color = self.rng.uniform(0.05, 0.95, size=3)
        self.model.geom_rgba[self.cube_geom_id, :3] = color
        self.model.geom_rgba[self.cube_geom_id, 3] = 1.0

    def _get_observation(self) -> dict[str, Any]:
        joint_pos = np.array([self.data.qpos[self.model.jnt_qposadr[jid]] for jid in self.joint_ids])
        joint_vel = np.array([self.data.qvel[self.model.jnt_dofadr[jid]] for jid in self.joint_ids])
        cube_pos = self.data.xpos[self.cube_body_id].copy()
        cube_quat = self.data.xquat[self.cube_body_id].copy()
        ee_pos = self.data.site_xpos[self.ee_site_id].copy()

        return {
            "observation.state": joint_pos.astype(np.float32),
            "observation.velocity": joint_vel.astype(np.float32),
            "observation.images.scene": self.render("scene"),
            "observation.images.wrist": self.render("wrist"),
            "state": {
                "cube_position": cube_pos.astype(np.float32),
                "cube_orientation": cube_quat.astype(np.float32),
                "ee_position": ee_pos.astype(np.float32),
            },
        }

    def _compute_reward(self, obs: dict[str, Any]) -> float:
        cube_z = float(obs["state"]["cube_position"][2])
        return max(0.0, cube_z - 0.03)

    def _update_abstract_grasp(self, action: np.ndarray) -> None:
        if not self.config.abstract_grasp:
            return

        gripper = float(action[-1])
        cube_pos = self.data.xpos[self.cube_body_id].copy()
        ee_pos = self.data.site_xpos[self.ee_site_id].copy()

        if self._grasped and gripper > self.config.open_gripper_threshold:
            self._grasped = False
            self._zero_cube_velocity()
            return

        if not self._grasped and gripper < self.config.closed_gripper_threshold:
            if np.linalg.norm(cube_pos - ee_pos) < self.config.grasp_threshold:
                self._grasped = True

        if self._grasped:
            cube_qpos = self._cube_qpos_slice()
            attached_pos = ee_pos.copy()
            attached_pos[2] -= self.config.grasp_offset_z
            self.data.qpos[cube_qpos] = np.array(
                [attached_pos[0], attached_pos[1], attached_pos[2], 1.0, 0.0, 0.0, 0.0]
            )
            self._zero_cube_velocity()

    def _clip_action(self, action: np.ndarray) -> np.ndarray:
        lowers = np.array([joint.lower for joint in self.robot.joint_specs])
        uppers = np.array([joint.upper for joint in self.robot.joint_specs])
        return np.clip(action, lowers, uppers)

    def _set_robot_qpos(self, qpos: np.ndarray) -> None:
        for joint_id, value in zip(self.joint_ids, qpos):
            self.data.qpos[self.model.jnt_qposadr[joint_id]] = value
            self.data.qvel[self.model.jnt_dofadr[joint_id]] = 0.0

    def _zero_cube_velocity(self) -> None:
        joint_id = self.model.joint("cube_freejoint").id
        start = self.model.jnt_dofadr[joint_id]
        self.data.qvel[start : start + 6] = 0.0

    def _cube_qpos_slice(self) -> slice:
        joint_id = self.model.joint("cube_freejoint").id
        start = self.model.jnt_qposadr[joint_id]
        return slice(start, start + 7)


if __name__ == "__main__":
    env = SOArm101CubePickEnv(seed=0)
    obs = env.reset()
    action = obs["observation.state"]
    obs, reward, terminated, truncated, info = env.step(action)
    print(
        {
            "state_shape": obs["observation.state"].shape,
            "image_shape": obs["observation.images.scene"].shape,
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "info": info,
        }
    )
    env.close()
