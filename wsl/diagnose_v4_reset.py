import csv
import json
import os
from pathlib import Path


JOINTS = [
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
]


POLICY = Path(
    "/mnt/f/CC-project/lerobot-storage/outputs/real_test_candidates/"
    "act_v4_050000/act_bottle_place_v4/checkpoints/050000/pretrained_model"
)
OUT = Path("/mnt/c/Users/ASUS/Documents/lerobot/rollout_analysis")


def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text())


def find_paths():
    candidates = {
        "wsl_dataset_cache": Path.home()
        / ".cache/huggingface/lerobot/datasets/RItcheOhe/so101_bottle_place_v4",
        "wsl_calibration": Path.home()
        / ".cache/huggingface/lerobot/calibration/robots/so_follower/R12260101.json",
        "windows_calibration": Path(
            "/mnt/c/Users/ASUS/Documents/lerobot/calibration/R12260101.json"
        ),
        "policy": POLICY,
    }
    return {k: {"path": str(v), "exists": v.exists()} for k, v in candidates.items()}


def latest_rollout_csvs():
    root = Path.home() / "lerobot_outputs/rollouts"
    if not root.exists():
        return []
    rows = []
    for path in root.glob("v4_*.csv"):
        rows.append(
            {
                "path": str(path),
                "mtime": path.stat().st_mtime,
                "size": path.stat().st_size,
            }
        )
    return sorted(rows, key=lambda r: r["mtime"], reverse=True)[:10]


def summarize_csv(path: Path):
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return {"rows": 0}
    first = rows[0]
    last = rows[-1]
    out = {"rows": len(rows), "first": {}, "last": {}, "min": {}, "max": {}}
    for joint in JOINTS:
        key = joint
        vals = []
        for row in rows:
            try:
                vals.append(float(row[key]))
            except Exception:
                pass
        if vals:
            out["first"][joint] = vals[0]
            out["last"][joint] = vals[-1]
            out["min"][joint] = min(vals)
            out["max"][joint] = max(vals)
    events = []
    thresholds = [10, 20, 30, 35]
    for threshold in thresholds:
        for index, row in enumerate(rows):
            try:
                gripper = float(row["gripper.pos"])
            except Exception:
                continue
            if gripper >= threshold:
                event = {"event": f"first_gripper_ge_{threshold}", "index": index}
                for key in ["t_wall", *JOINTS]:
                    try:
                        event[key] = float(row[key])
                    except Exception:
                        pass
                events.append(event)
                break
    if "shoulder_lift.pos" in out["max"]:
        target = out["max"]["shoulder_lift.pos"]
        for index, row in enumerate(rows):
            try:
                if float(row["shoulder_lift.pos"]) == target:
                    event = {"event": "max_shoulder_lift", "index": index}
                    for key in ["t_wall", *JOINTS]:
                        try:
                            event[key] = float(row[key])
                        except Exception:
                            pass
                    events.append(event)
                    break
            except Exception:
                pass
    out["events"] = events
    return out


def read_safetensors_stats():
    stats = {"available": False, "keys": [], "error": None}
    try:
        from safetensors import safe_open
    except Exception as exc:
        stats["error"] = f"safetensors import failed: {exc}"
        return stats

    path = POLICY / "policy_preprocessor_step_3_normalizer_processor.safetensors"
    if not path.exists():
        stats["error"] = f"missing {path}"
        return stats

    try:
        with safe_open(str(path), framework="pt", device="cpu") as f:
            keys = list(f.keys())
            stats["available"] = True
            stats["keys"] = keys
            selected = {}
            for key in keys:
                lk = key.lower()
                if "observation.state" in lk or "state" in lk:
                    tensor = f.get_tensor(key)
                    selected[key] = [float(x) for x in tensor.flatten().tolist()]
            stats["selected"] = selected
    except Exception as exc:
        stats["error"] = str(exc)
    return stats


def maybe_read_dataset_first_rows():
    root = Path.home() / ".cache/huggingface/lerobot/datasets/RItcheOhe/so101_bottle_place_v4"
    out = {"root": str(root), "exists": root.exists()}
    if not root.exists():
        return out
    parquet_files = list(root.rglob("*.parquet"))
    out["parquet_files"] = [str(p) for p in parquet_files[:10]]
    try:
        import pyarrow.parquet as pq
    except Exception as exc:
        out["error"] = f"pyarrow import failed: {exc}"
        return out
    if parquet_files:
        table = pq.read_table(parquet_files[0], columns=["observation.state"])
        rows = table.slice(0, 5).to_pylist()
        out["first_observation_state_rows"] = rows
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = {
        "paths": find_paths(),
        "policy_config": read_json(POLICY / "config.json"),
        "train_config": read_json(POLICY / "train_config.json"),
        "current_calibration_windows": read_json(
            Path("/mnt/c/Users/ASUS/Documents/lerobot/calibration/R12260101.json")
        ),
        "current_calibration_wsl_cache": read_json(
            Path.home()
            / ".cache/huggingface/lerobot/calibration/robots/so_follower/R12260101.json"
        ),
        "latest_rollout_csvs": latest_rollout_csvs(),
        "normalizer_stats": read_safetensors_stats(),
        "dataset_probe": maybe_read_dataset_first_rows(),
    }
    csvs = result["latest_rollout_csvs"]
    if csvs:
        result["latest_rollout_summary"] = summarize_csv(Path(csvs[0]["path"]))

    json_path = OUT / "v4_reset_diagnosis.json"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    md = []
    md.append("# V4 Reset Diagnosis\n")
    md.append("## Paths\n")
    for name, item in result["paths"].items():
        md.append(f"- {name}: {item['exists']} `{item['path']}`")
    md.append("\n## Latest V4 CSVs\n")
    for row in result["latest_rollout_csvs"]:
        md.append(f"- `{row['path']}` size={row['size']}")
    if "latest_rollout_summary" in result:
        s = result["latest_rollout_summary"]
        md.append("\n## Latest Rollout First/Last State\n")
        md.append(f"- rows: {s.get('rows')}")
        for joint in JOINTS:
            if joint in s.get("first", {}):
                md.append(
                    f"- {joint}: first={s['first'][joint]:.3f}, "
                    f"last={s['last'][joint]:.3f}, "
                    f"min={s['min'][joint]:.3f}, max={s['max'][joint]:.3f}"
                )
        md.append("\n## Latest Rollout Events\n")
        for event in s.get("events", []):
            fields = [f"- {event['event']} index={event['index']}"]
            for joint in JOINTS:
                if joint in event:
                    fields.append(f"{joint}={event[joint]:.3f}")
            md.append(", ".join(fields))
    md.append("\n## Normalizer\n")
    md.append(f"- available: {result['normalizer_stats'].get('available')}")
    md.append(f"- error: {result['normalizer_stats'].get('error')}")
    md.append("- keys:")
    for key in result["normalizer_stats"].get("keys", []):
        md.append(f"  - `{key}`")
    md.append("\n## Dataset Probe\n")
    md.append(json.dumps(result["dataset_probe"], indent=2, ensure_ascii=False))

    md_path = OUT / "v4_reset_diagnosis.md"
    md_path.write_text("\n".join(md))
    print(f"WROTE {json_path}")
    print(f"WROTE {md_path}")


if __name__ == "__main__":
    main()
