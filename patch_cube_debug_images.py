from pathlib import Path
p = Path('/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py')
s = p.read_text()
bak = p.with_suffix(p.suffix + '.bak_cube_debug_images')
if not bak.exists():
    bak.write_text(s)
old = '''                    center, area = _detect_cube_center(rgb, detect_mode)
                    writer.writerow([
'''
new = '''                    center, area = _detect_cube_center(rgb, detect_mode)
                    debug_dir = os.environ.get("ROLLOUT_CUBE_DEBUG_IMAGE_DIR")
                    if debug_dir:
                        try:
                            from pathlib import Path as _Path
                            from PIL import Image as _Image, ImageDraw as _ImageDraw

                            max_images = int(float(os.environ.get("ROLLOUT_CUBE_DEBUG_MAX_IMAGES", "20") or 20))
                            saved_count = int(getattr(send_next_action, "_codex_cube_debug_saved_count", 0) or 0)
                            stride = int(float(os.environ.get("ROLLOUT_CUBE_DEBUG_STRIDE", "10") or 10))
                            seen_count = int(getattr(send_next_action, "_codex_cube_debug_seen_count", 0) or 0)
                            send_next_action._codex_cube_debug_seen_count = seen_count + 1
                            if saved_count < max_images and (seen_count % max(1, stride) == 0):
                                out_dir = _Path(debug_dir)
                                out_dir.mkdir(parents=True, exist_ok=True)
                                img = _Image.fromarray(rgb)
                                draw = _ImageDraw.Draw(img)
                                if center is not None:
                                    draw.rectangle([center["x_min"], center["y_min"], center["x_max"], center["y_max"]], outline=(255, 0, 0), width=2)
                                    draw.ellipse([center["cx"] - 2, center["cy"] - 2, center["cx"] + 2, center["cy"] + 2], fill=(255, 0, 0))
                                safe_camera = str(camera_key).replace("/", "_").replace(".", "_")
                                img.save(out_dir / f"{saved_count:03d}_{safe_camera}_{detect_mode}.png")
                                send_next_action._codex_cube_debug_saved_count = saved_count + 1
                        except Exception as exc:
                            if os.environ.get("ROLLOUT_DEBUG_CUBE_CENTER", "0") == "1":
                                print(f"[CUBE DEBUG IMAGE ERROR] {exc}", flush=True)
                    writer.writerow([
'''
if old not in s:
    raise SystemExit('debug image insertion point not found')
s=s.replace(old,new,1)
p.write_text(s)
print('patched cube debug image saving')
