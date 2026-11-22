from pathlib import Path
p = Path('/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py')
s = p.read_text()
bak = p.with_suffix(p.suffix + '.bak_cube_cc_detector')
if not bak.exists():
    bak.write_text(s)
old = '''        def _detect_cube_center(rgb, mode):
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
'''
new = '''        def _largest_component(mask):
            mask = np.asarray(mask, dtype=bool)
            h_img, w_img = mask.shape[:2]
            visited = np.zeros((h_img, w_img), dtype=bool)
            best = None
            best_area = 0
            ys0, xs0 = np.nonzero(mask)
            for y0, x0 in zip(ys0.tolist(), xs0.tolist()):
                if visited[y0, x0]:
                    continue
                stack = [(y0, x0)]
                visited[y0, x0] = True
                xs = []
                ys = []
                while stack:
                    y, x = stack.pop()
                    xs.append(x)
                    ys.append(y)
                    for ny in (y - 1, y, y + 1):
                        for nx in (x - 1, x, x + 1):
                            if ny == y and nx == x:
                                continue
                            if ny < 0 or nx < 0 or ny >= h_img or nx >= w_img:
                                continue
                            if visited[ny, nx] or not mask[ny, nx]:
                                continue
                            visited[ny, nx] = True
                            stack.append((ny, nx))
                area = len(xs)
                if area > best_area:
                    best_area = area
                    best = (np.asarray(xs, dtype=np.float32), np.asarray(ys, dtype=np.float32))
            return best, best_area

        def _detect_cube_center(rgb, mode):
            h, s, v = _rgb_to_hsv_np(rgb)
            mode = (mode or "auto").lower()
            if mode == "custom_hsv":
                h_min = float(os.environ.get("ROLLOUT_CUBE_H_MIN", "0") or 0)
                h_max = float(os.environ.get("ROLLOUT_CUBE_H_MAX", "360") or 360)
                s_min = float(os.environ.get("ROLLOUT_CUBE_S_MIN", "0") or 0)
                s_max = float(os.environ.get("ROLLOUT_CUBE_S_MAX", "1") or 1)
                v_min = float(os.environ.get("ROLLOUT_CUBE_V_MIN", "0") or 0)
                v_max = float(os.environ.get("ROLLOUT_CUBE_V_MAX", "1") or 1)
                if h_min <= h_max:
                    h_mask = (h >= h_min) & (h <= h_max)
                else:
                    h_mask = (h >= h_min) | (h <= h_max)
                mask = h_mask & (s >= s_min) & (s <= s_max) & (v >= v_min) & (v <= v_max)
            elif mode == "red":
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
            total_area = int(mask.sum())
            component, area = _largest_component(mask)
            min_area = int(float(os.environ.get("ROLLOUT_CUBE_MIN_AREA", "20") or 20))
            if component is None or area < min_area:
                return None, total_area
            xs, ys = component
            h_img, w_img = rgb.shape[:2]
            x_min, x_max = float(xs.min()), float(xs.max())
            y_min, y_max = float(ys.min()), float(ys.max())
            cx = float((x_min + x_max) / 2.0)
            cy = float((y_min + y_max) / 2.0)
            bbox_area = max(1.0, (x_max - x_min + 1.0) * (y_max - y_min + 1.0))
            fill_ratio = float(area / bbox_area)
            confidence = float(min(1.0, area / max(1.0, min_area)) * min(1.0, fill_ratio * 2.0))
            return {
                "cx": cx,
                "cy": cy,
                "err_x": cx - (w_img - 1) / 2.0,
                "err_y": cy - (h_img - 1) / 2.0,
                "w": int(w_img),
                "h": int(h_img),
                "component_area": int(area),
                "total_area": int(total_area),
                "x_min": x_min,
                "y_min": y_min,
                "x_max": x_max,
                "y_max": y_max,
                "fill_ratio": fill_ratio,
                "confidence": confidence,
            }, total_area
'''
if old not in s:
    raise SystemExit('detector block not found')
s=s.replace(old,new,1)
s=s.replace('''                        "image_h",\n                        "close_candidate",''','''                        "image_h",\n                        "component_area",\n                        "total_area",\n                        "x_min",\n                        "y_min",\n                        "x_max",\n                        "y_max",\n                        "fill_ratio",\n                        "confidence",\n                        "close_candidate",''')
s=s.replace('''                        "" if center is None else center["h"],\n                        bool(locals().get("close_candidate", False)),''','''                        "" if center is None else center["h"],\n                        "" if center is None else center["component_area"],\n                        area,\n                        "" if center is None else center["x_min"],\n                        "" if center is None else center["y_min"],\n                        "" if center is None else center["x_max"],\n                        "" if center is None else center["y_max"],\n                        "" if center is None else center["fill_ratio"],\n                        "" if center is None else center["confidence"],\n                        bool(locals().get("close_candidate", False)),''')
p.write_text(s)
print('patched cube connected component detector')
