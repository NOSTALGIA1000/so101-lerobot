import argparse
import time
from pathlib import Path

import cv2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-index", type=int, default=6)
    parser.add_argument("--out-dir", default=r"C:\Users\ASUS\Documents\lerobot\camera_probe_live")
    args = parser.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    opened = []
    for idx in range(args.max_index):
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print(f"index {idx}: not opened")
            cap.release()
            continue

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        time.sleep(0.4)
        ok, frame = cap.read()
        if ok and frame is not None:
            cv2.putText(
                frame,
                f"OpenCV index {idx}",
                (24, 48),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.1,
                (0, 255, 0),
                3,
            )
            path = out / f"camera_{idx}.jpg"
            cv2.imwrite(str(path), frame)
            print(f"index {idx}: OK -> {path}")
            opened.append(idx)
        else:
            print(f"index {idx}: opened but no frame")
        cap.release()

    print("opened_indices=", opened)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
