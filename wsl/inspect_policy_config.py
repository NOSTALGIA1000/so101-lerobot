import json
import sys
from pathlib import Path


KEYWORDS = (
    "feature",
    "image",
    "camera",
    "dataset",
    "repo",
    "input",
    "output",
    "normal",
    "action",
    "robot",
    "state",
)


def walk(obj, prefix=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}{key}"
            if any(word in str(key).lower() for word in KEYWORDS):
                if isinstance(value, (dict, list)):
                    print(f"{path} = {type(value).__name__}")
                else:
                    print(f"{path} = {value!r}")
            walk(value, path + ".")
    elif isinstance(obj, list):
        for index, value in enumerate(obj[:8]):
            walk(value, f"{prefix}{index}.")


def main() -> int:
    base = Path(sys.argv[1])
    for name in (
        "config.json",
        "train_config.json",
        "policy_preprocessor.json",
        "policy_postprocessor.json",
    ):
        path = base / name
        print(f"--- {path}")
        if not path.exists():
            print("missing")
            continue
        walk(json.loads(path.read_text()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
