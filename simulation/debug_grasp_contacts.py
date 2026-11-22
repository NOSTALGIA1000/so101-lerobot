"""Debug SO-101 gripper contacts with the cube."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SIM_DEPS = REPO_ROOT / ".sim_deps"
if SIM_DEPS.exists() and str(SIM_DEPS) not in sys.path:
    sys.path.insert(0, str(SIM_DEPS))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from simulation.dataset_generation.generate_expert_dataset import SO101CubeExpert, ExpertConfig
from simulation.environments.soarm101_cube_pick_env import SOArm101CubePickEnv


def main() -> None:
    env = SOArm101CubePickEnv(seed=0)
    obs = env.reset()
    expert = SO101CubeExpert(env, ExpertConfig(use_grasp_assist=False))
    commands = expert.plan_episode()
    finger_names = {"fixed_finger_pad", "moving_finger_pad"}
    ee_site = env.model.site("ee_site").id
    fixed_site = env.model.site("fixed_finger_site").id
    moving_site = env.model.site("moving_finger_site").id

    for step, command in enumerate(commands):
        obs, _reward, _terminated, _truncated, _info = env.step(command.action)
        contact_pairs = []
        for idx in range(env.data.ncon):
            contact = env.data.contact[idx]
            g1 = env.model.geom(contact.geom1).name
            g2 = env.model.geom(contact.geom2).name
            if "cube_geom" in (g1, g2) and (g1 in finger_names or g2 in finger_names):
                contact_pairs.append((g1, g2))
        if step % 20 == 0 or contact_pairs:
            cube_z = float(obs["state"]["cube_position"][2])
            cube_pos = obs["state"]["cube_position"]
            ee_dist = float(np.linalg.norm(env.data.site_xpos[ee_site] - cube_pos))
            fixed_dist = float(np.linalg.norm(env.data.site_xpos[fixed_site] - cube_pos))
            moving_dist = float(np.linalg.norm(env.data.site_xpos[moving_site] - cube_pos))
            q = obs["observation.state"]
            q_error = command.action - q
            print(
                "step",
                step,
                "cube_z",
                round(cube_z, 4),
                "gripper",
                round(float(q[-1]), 4),
                "qerr_norm",
                round(float(np.linalg.norm(q_error)), 4),
                "dist",
                {
                    "ee": round(ee_dist, 4),
                    "fixed": round(fixed_dist, 4),
                    "moving": round(moving_dist, 4),
                },
                "contacts",
                contact_pairs[:6],
            )
    env.close()


if __name__ == "__main__":
    main()
