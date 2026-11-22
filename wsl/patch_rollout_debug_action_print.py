#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


CORE = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
BACKUP = CORE.with_suffix(".py.codex_debug_action_backup")

OLD = """    if len(interp) != len(ordered_keys):
        raise ValueError(f"Interpolated tensor length ({len(interp)}) != action keys ({len(ordered_keys)})")
    action_dict = {k: interp[i].item() for i, k in enumerate(ordered_keys)}

    # Codex SO-ARM101 real-test gripper postprocess.
"""

NEW = """    if len(interp) != len(ordered_keys):
        raise ValueError(f"Interpolated tensor length ({len(interp)}) != action keys ({len(ordered_keys)})")
    action_dict = {k: interp[i].item() for i, k in enumerate(ordered_keys)}

    # Optional Codex action debug printing.
    # Enable with ROLLOUT_DEBUG_ACTION=1.
    # This prints the ACT action trajectory before robot_action_processor and
    # before any optional gripper postprocess below.
    import os

    if os.environ.get("ROLLOUT_DEBUG_ACTION", "0") == "1":
        import time

        if not getattr(send_next_action, "_codex_printed_ordered_keys", False):
            print("[ACT ORDERED_KEYS] " + ", ".join(str(k) for k in ordered_keys), flush=True)
            send_next_action._codex_printed_ordered_keys = True
        print("[ACT ACTION]", flush=True)
        print(f"time={time.time():.6f}", flush=True)
        for k in ordered_keys:
            print(f"{k}={action_dict[k]:.6f}", flush=True)

    # Codex SO-ARM101 real-test gripper postprocess.
"""


def main() -> None:
    text = CORE.read_text()
    if NEW in text:
        print(f"already_patched={CORE}")
        return
    if OLD not in text:
        raise RuntimeError("target snippet not found; refusing to patch")
    if not BACKUP.exists():
        BACKUP.write_text(text)
        print(f"backup={BACKUP}")
    CORE.write_text(text.replace(OLD, NEW))
    print(f"patched={CORE}")


if __name__ == "__main__":
    main()
