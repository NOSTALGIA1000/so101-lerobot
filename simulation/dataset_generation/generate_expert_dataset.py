"""Generate lightweight expert demonstrations for SO-101 cube pick.

The first output format is intentionally dependency-light:

- `meta/info.json`
- `episodes/episode_000000.npz`

Each NPZ contains arrays compatible with the local LeRobot feature names:

- `observation.state`
- `observation.velocity`
- `action`
- `cube_position`
- `cube_orientation`
- `timestamp`
- `frame_index`
- `episode_index`
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DEPS = REPO_ROOT / ".sim_deps"
if SIM_DEPS.exists() and str(SIM_DEPS) not in sys.path:
    sys.path.insert(0, str(SIM_DEPS))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import mujoco  # noqa: E402

from simulation.environments.soarm101_cube_pick_env import SOArm101CubePickEnv


@dataclass(frozen=True)
class ExpertConfig:
    fps: int = 30
    steps_per_segment: int = 60
    ik_iterations: int = 80
    ik_damping: float = 1e-3
    max_ik_step: float = 0.08
    grasp_offset_z: float = 0.055
    place_position: tuple[float, float, float] = (0.18, -0.16, 0.035)
    grasp_target_offset: tuple[float, float, float] = (0.031, 0.007, -0.004)
    use_grasp_assist: bool = False
    use_release_assist: bool = False


@dataclass(frozen=True)
class ExpertCommand:
    action: np.ndarray
    grasp_assist: bool = False
    release: bool = False


class SO101CubeExpert:
    def __init__(self, env: SOArm101CubePickEnv, config: ExpertConfig | None = None) -> None:
        self.env = env
        self.config = config or ExpertConfig(fps=env.config.fps)
        self.ee_site_id = self.env.model.site("ee_site").id
        self.arm_joint_ids = self.env.joint_ids[:5]
        self.arm_qpos_addrs = [self.env.model.jnt_qposadr[jid] for jid in self.arm_joint_ids]

    def plan_episode(self) -> list[ExpertCommand]:
        obs = self.env._get_observation()
        cube_pos = obs["state"]["cube_position"].astype(np.float64)

        open_gripper = self.env.robot.joint_specs[-1].upper
        closed_gripper = self.env.robot.joint_specs[-1].lower
        current = obs["observation.state"].astype(np.float64)

        grasp_offset = np.array(self.config.grasp_target_offset)
        grasp_target = cube_pos + grasp_offset

        targets = [
            (grasp_target + np.array([0.0, 0.0, 0.13]), open_gripper, False, False),
            (grasp_target + np.array([0.0, 0.0, 0.040]), open_gripper, False, False),
            (grasp_target, closed_gripper, False, False),
            (grasp_target + np.array([0.0, 0.0, 0.13]), closed_gripper, True, False),
            (np.array([0.18, -0.16, 0.15]), closed_gripper, True, False),
            (np.array([0.18, -0.16, 0.06]), closed_gripper, True, False),
            (np.array([0.18, -0.16, 0.06]), open_gripper, False, True),
        ]

        commands: list[ExpertCommand] = []
        q = current.copy()
        for target_pos, gripper, grasp_assist, release in targets:
            q_target = self._solve_ik(target_pos, q)
            q_target[-1] = gripper
            for action in self._interpolate(q, q_target):
                commands.append(ExpertCommand(action=action, grasp_assist=grasp_assist, release=release))
            q = q_target
        return commands

    def _interpolate(self, start: np.ndarray, end: np.ndarray) -> list[np.ndarray]:
        segment = []
        for alpha in np.linspace(0.0, 1.0, self.config.steps_per_segment, endpoint=False)[1:]:
            segment.append((1.0 - alpha) * start + alpha * end)
        segment.append(end.copy())
        return segment

    def _solve_ik(self, target_pos: np.ndarray, seed_q: np.ndarray) -> np.ndarray:
        q = seed_q.copy()
        q[-1] = self.env.robot.joint_specs[-1].upper

        for _ in range(self.config.ik_iterations):
            self._set_robot_qpos(q)
            mujoco.mj_forward(self.env.model, self.env.data)

            ee_pos = self.env.data.site_xpos[self.ee_site_id].copy()
            error = target_pos - ee_pos
            if np.linalg.norm(error) < 0.008:
                break

            jacp = np.zeros((3, self.env.model.nv))
            jacr = np.zeros((3, self.env.model.nv))
            mujoco.mj_jacSite(self.env.model, self.env.data, jacp, jacr, self.ee_site_id)
            jac = jacp[:, [self.env.model.jnt_dofadr[jid] for jid in self.arm_joint_ids]]
            jt = jac.T
            lhs = jac @ jt + self.config.ik_damping * np.eye(3)
            dq = jt @ np.linalg.solve(lhs, error)
            norm = np.linalg.norm(dq)
            if norm > self.config.max_ik_step:
                dq *= self.config.max_ik_step / norm

            for idx, delta in enumerate(dq):
                q[idx] += delta
            q = self.env._clip_action(q)

        return q

    def _set_robot_qpos(self, q: np.ndarray) -> None:
        for joint_id, value in zip(self.env.joint_ids, q):
            self.env.data.qpos[self.env.model.jnt_qposadr[joint_id]] = value

    def apply_grasp_assist(self) -> None:
        ee_pos = self.env.data.site_xpos[self.ee_site_id].copy()
        cube_qpos = self.env._cube_qpos_slice()
        cube_pos = ee_pos.copy()
        cube_pos[2] -= self.config.grasp_offset_z
        self.env.data.qpos[cube_qpos] = np.array([cube_pos[0], cube_pos[1], cube_pos[2], 1.0, 0.0, 0.0, 0.0])
        self._zero_cube_velocity()
        mujoco.mj_forward(self.env.model, self.env.data)

    def apply_release_assist(self) -> None:
        cube_qpos = self.env._cube_qpos_slice()
        x, y, z = self.config.place_position
        self.env.data.qpos[cube_qpos] = np.array([x, y, z, 1.0, 0.0, 0.0, 0.0])
        self._zero_cube_velocity()
        mujoco.mj_forward(self.env.model, self.env.data)

    def _zero_cube_velocity(self) -> None:
        joint_id = self.env.model.joint("cube_freejoint").id
        start = self.env.model.jnt_dofadr[joint_id]
        self.env.data.qvel[start : start + 6] = 0.0


def generate_dataset(output_dir: Path, episodes: int, seed: int, use_grasp_assist: bool, use_release_assist: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    episode_dir = output_dir / "episodes"
    episode_dir.mkdir(parents=True, exist_ok=True)

    env = SOArm101CubePickEnv(seed=seed)
    expert = SO101CubeExpert(
        env,
        ExpertConfig(use_grasp_assist=use_grasp_assist, use_release_assist=use_release_assist),
    )
    episode_lengths: list[int] = []

    for episode_index in range(episodes):
        obs = env.reset()
        commands = expert.plan_episode()

        states = []
        velocities = []
        cube_positions = []
        cube_orientations = []
        ee_positions = []
        executed_actions = []
        rewards = []
        successes = []

        for command in commands:
            action = command.action
            states.append(obs["observation.state"])
            velocities.append(obs["observation.velocity"])
            cube_positions.append(obs["state"]["cube_position"])
            cube_orientations.append(obs["state"]["cube_orientation"])
            ee_positions.append(obs["state"]["ee_position"])
            executed_actions.append(action.astype(np.float32))

            obs, reward, terminated, _truncated, info = env.step(action)
            if command.grasp_assist and expert.config.use_grasp_assist:
                expert.apply_grasp_assist()
                obs = env._get_observation()
                reward = env._compute_reward(obs)
                terminated = bool(obs["state"]["cube_position"][2] > 0.08)
                info = {"is_success": terminated, "grasp_assist": True}
            elif command.release and expert.config.use_release_assist:
                expert.apply_release_assist()
                obs = env._get_observation()
            rewards.append(np.float32(reward))
            successes.append(bool(info["is_success"] or terminated))

        frame_count = len(executed_actions)
        episode_lengths.append(frame_count)
        timestamps = np.arange(frame_count, dtype=np.float32) / env.config.fps

        np.savez_compressed(
            episode_dir / f"episode_{episode_index:06d}.npz",
            **{
                "observation.state": np.asarray(states, dtype=np.float32),
                "observation.velocity": np.asarray(velocities, dtype=np.float32),
                "action": np.asarray(executed_actions, dtype=np.float32),
                "cube_position": np.asarray(cube_positions, dtype=np.float32),
                "cube_orientation": np.asarray(cube_orientations, dtype=np.float32),
                "ee_position": np.asarray(ee_positions, dtype=np.float32),
                "reward": np.asarray(rewards, dtype=np.float32),
                "success": np.asarray(successes, dtype=np.bool_),
                "timestamp": timestamps,
                "frame_index": np.arange(frame_count, dtype=np.int64),
                "episode_index": np.full(frame_count, episode_index, dtype=np.int64),
            },
        )

    env.close()
    info = {
        "codebase_version": "sim-step5-lightweight",
        "robot_type": "so101",
        "task": "SO-101 pick cube in MuJoCo",
        "fps": 30,
        "total_episodes": episodes,
        "total_frames": int(sum(episode_lengths)),
        "episode_lengths": episode_lengths,
        "features": {
            "action": {
                "dtype": "float32",
                "shape": [6],
                "names": list(env.robot.action_keys),
            },
            "observation.state": {
                "dtype": "float32",
                "shape": [6],
                "names": list(env.robot.state_keys),
            },
            "cube_position": {"dtype": "float32", "shape": [3]},
            "cube_orientation": {"dtype": "float32", "shape": [4]},
            "ee_position": {"dtype": "float32", "shape": [3]},
        },
        "expert": {
            "use_grasp_assist": use_grasp_assist,
            "use_release_assist": use_release_assist,
            "env_abstract_grasp": env.config.abstract_grasp,
        },
    }
    meta_dir = output_dir / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "simulation" / "outputs" / "expert_dataset_smoke")
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--enable-grasp-assist", action="store_true")
    parser.add_argument("--enable-release-assist", action="store_true")
    args = parser.parse_args()

    generate_dataset(
        args.output_dir,
        args.episodes,
        args.seed,
        use_grasp_assist=args.enable_grasp_assist,
        use_release_assist=args.enable_release_assist,
    )
    print(f"generated={args.output_dir}")


if __name__ == "__main__":
    main()
