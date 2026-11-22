import argparse
import csv
from pathlib import Path


def to_float(value: str):
    try:
        return float(value)
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    args = parser.parse_args()

    path = Path(args.csv_path).expanduser()
    print(f"path={path}")
    if not path.exists():
        print("exists=false")
        return 2

    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))

    print(f"rows={len(rows)}")
    if not rows:
        return 0

    print("columns=" + ",".join(rows[0].keys()))
    for key in rows[0].keys():
        vals = [to_float(row.get(key, "")) for row in rows]
        vals = [v for v in vals if v is not None]
        if not vals:
            continue
        print(
            f"{key}: min={min(vals):.3f} max={max(vals):.3f} "
            f"first={vals[0]:.3f} last={vals[-1]:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
