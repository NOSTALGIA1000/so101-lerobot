#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


CORE = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
BACKUP = CORE.with_suffix(".py.codex_action_logging_backup")

OLD = """    processed = ctx.processors.robot_action_processor((action_dict, obs_raw))
    ctx.hardware.robot_wrapper.send_action(processed)
    return action_dict
"""

NEW = """    # Optional Codex action trajectory logging.
    action_log_path = os.environ.get("ROLLOUT_ACTION_LOG_PATH")
    if action_log_path:
        import time
        from pathlib import Path

        log_path = Path(action_log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not log_path.exists()
        with log_path.open("a", encoding="utf-8") as f:
            if write_header:
                f.write("t_wall," + ",".join(action_dict.keys()) + "\\n")
            f.write(str(time.time()) + "," + ",".join(str(action_dict[k]) for k in action_dict.keys()) + "\\n")

    processed = ctx.processors.robot_action_processor((action_dict, obs_raw))
    ctx.hardware.robot_wrapper.send_action(processed)
    return action_dict
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
