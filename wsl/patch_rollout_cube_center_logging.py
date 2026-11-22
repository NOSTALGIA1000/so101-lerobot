from pathlib import Path

core = Path("/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py")
text = core.read_text(encoding="utf-8")

marker = '''    # Optional Codex action trajectory logging.
    action_log_path = os.environ.get("ROLLOUT_ACTION_LOG_PATH")
'''

insert = r'''    # Optional cube center visual logging.
    # Default off. This only records visual error; it does not control robot.
    # Enable with:
    #   ROLLOUT_CUBE_CENTER_LOG_PATH=...
    # Optional:
    #   ROLLOUT_CUBE_CENTER_CAMERA=wrist|scene|all
    #   ROLLOUT_CUBE_DETECT_MODE=auto|red|green|blue|bright|dark
    cube_center_log_path = os.environ.get("ROLLOUT_CUBE_CENTER_LOG_PATH")
    if cube_center_log_path:
        import csv
        import time
        from pathlib import Path

        import numpy as np

        def _as_numpy_image(value):
            try:
                import torch

                if isinstance(value, torch.Tensor):
                    value = value.detach().cpu().numpy()
            except Exception:
                pass
            try:
                from PIL import Image

                if isinstance(value, Image.Image):
                    value = np.asarray(value)
            except Exception:
                pass
            arr = np.asarray(value)
            if arr.ndim == 3 and arr.shape[0] in (1, 3, 4) and arr.shape[-1] not in (1, 3, 4):
                arr = np.moveaxis(arr, 0, -1)
            if arr.ndim == 2:
                arr = np.repeat(arr[..., None], 3, axis=2)
            if arr.ndim != 3 or arr.shape[2] < 3:
                return None
            arr = arr[..., :3]
            if arr.dtype != np.uint8:
                # Handle normalized float CHW/HWC images.
                maxv = float(np.nanmax(arr)) if arr.size else 1.0
                if maxv <= 1.5:
                    arr = arr * 255.0
                arr = np.clip(arr, 0, 255).astype(np.uint8)
            return arr

        def _rgb_to_hsv_np(rgb):
            arr = rgb.astype(np.float32) / 255.0
            r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
            mx = np.max(arr, axis=2)
            mn = np.min(arr, axis=2)
            diff = mx - mn
            h = np.zeros_like(mx)
            mask = diff > 1e-6
            rmask = mask & (mx == r)
            gmask = mask & (mx == g)
            bmask = mask & (mx == b)
            h[rmask] = (60.0 * ((g[rmask] - b[rmask]) / diff[rmask]) + 360.0) % 360.0
            h[gmask] = 60.0 * ((b[gmask] - r[gmask]) / diff[gmask] + 2.0)
            h[bmask] = 60.0 * ((r[bmask] - g[bmask]) / diff[bmask] + 4.0)
            s = np.zeros_like(mx)
            s[mx > 1e-6] = diff[mx > 1e-6] / mx[mx > 1e-6]
            v = mx
            return h, s, v

        def _detect_cube_center(rgb, mode):
            h, s, v = _rgb_to_hsv_np(rgb)
            mode = (mode or "auto").lower()
            if mode == "red":
                mask = (((h < 25.0) | (h > 335.0)) & (s > 0.25) & (v > 0.18))
            elif mode == "green":
                mask = ((h > 70.0) & (h < 170.0) & (s > 0.25) & (v > 0.18))
            elif mode == "blue":
                mask = ((h > 180.0) & (h < 270.0) & (s > 0.25) & (v > 0.18))
            elif mode == "bright":
                mask = ((v > 0.65) & (s < 0.55))
            elif mode == "dark":
                mask = (v < 0.25)
            else:
                # Prefer colored objects; fallback to bright objects.
                mask = ((s > 0.25) & (v > 0.20))
                if int(mask.sum()) < 20:
                    mask = ((v > 0.65) & (s < 0.55))
            ys, xs = np.nonzero(mask)
            area = int(xs.size)
            if area < int(float(os.environ.get("ROLLOUT_CUBE_MIN_AREA", "20") or 20)):
                return None, area
            h_img, w_img = rgb.shape[:2]
            cx = float(xs.mean())
            cy = float(ys.mean())
            return {
                "cx": cx,
                "cy": cy,
                "err_x": cx - (w_img - 1) / 2.0,
                "err_y": cy - (h_img - 1) / 2.0,
                "w": int(w_img),
                "h": int(h_img),
            }, area

        wanted_camera = os.environ.get("ROLLOUT_CUBE_CENTER_CAMERA", "wrist").strip().lower()
        detect_mode = os.environ.get("ROLLOUT_CUBE_DETECT_MODE", "auto").strip().lower()
        close_gate_active_for_log = bool(locals().get("close_candidate", False) or locals().get("allow_close", False))
        log_only_close = os.environ.get("ROLLOUT_CUBE_LOG_ONLY_CLOSE_GATE", "1") == "1"
        if (not log_only_close) or close_gate_active_for_log:
            image_items = []
            for key, value in obs_raw.items():
                key_lower = str(key).lower()
                if (
                    "image" in key_lower
                    or key_lower.endswith("wrist")
                    or key_lower.endswith("scene")
                    or key_lower.endswith("overhead")
                ):
                    if wanted_camera != "all" and wanted_camera not in key_lower:
                        continue
                    image_items.append((str(key), value))
            log_path = Path(cube_center_log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            write_header = not log_path.exists()
            with log_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow([
                        "t_wall",
                        "camera_key",
                        "detect_mode",
                        "area",
                        "cx",
                        "cy",
                        "err_x_px",
                        "err_y_px",
                        "image_w",
                        "image_h",
                        "close_candidate",
                        "allow_close",
                        "shoulder_pan",
                        "shoulder_lift",
                        "elbow_flex",
                        "wrist_flex",
                        "gripper",
                    ])
                for camera_key, image_value in image_items:
                    rgb = _as_numpy_image(image_value)
                    if rgb is None:
                        continue
                    center, area = _detect_cube_center(rgb, detect_mode)
                    writer.writerow([
                        time.time(),
                        camera_key,
                        detect_mode,
                        area,
                        "" if center is None else center["cx"],
                        "" if center is None else center["cy"],
                        "" if center is None else center["err_x"],
                        "" if center is None else center["err_y"],
                        "" if center is None else center["w"],
                        "" if center is None else center["h"],
                        bool(locals().get("close_candidate", False)),
                        bool(locals().get("allow_close", False)),
                        action_dict.get("shoulder_pan.pos", ""),
                        action_dict.get("shoulder_lift.pos", ""),
                        action_dict.get("elbow_flex.pos", ""),
                        action_dict.get("wrist_flex.pos", ""),
                        action_dict.get("gripper.pos", ""),
                    ])

'''

if "ROLLOUT_CUBE_CENTER_LOG_PATH" in text:
    print("ROLLOUT_CUBE_CENTER_LOG_PATH already present; no change")
elif marker not in text:
    raise SystemExit("marker not found")
else:
    core.write_text(text.replace(marker, insert + marker), encoding="utf-8")
    print("patched", core)
