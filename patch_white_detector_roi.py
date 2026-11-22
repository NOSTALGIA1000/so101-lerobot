from pathlib import Path
p=Path('/mnt/c/Users/ASUS/Documents/lerobot/wsl/detect_white_target_from_zmq.py')
s=p.read_text()
old='''def detect_white_target(bgr: np.ndarray, s_max: int, v_min: int, min_area: int):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    # OpenCV HSV: H 0..179, S/V 0..255
    mask = ((hsv[:, :, 1] <= s_max) & (hsv[:, :, 2] >= v_min)).astype(np.uint8)
'''
new='''def detect_white_target(bgr: np.ndarray, s_max: int, v_min: int, min_area: int, roi: tuple[float, float, float, float] | None = None):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    # OpenCV HSV: H 0..179, S/V 0..255
    mask = ((hsv[:, :, 1] <= s_max) & (hsv[:, :, 2] >= v_min)).astype(np.uint8)
    if roi is not None:
        img_h, img_w = mask.shape[:2]
        x0f, y0f, x1f, y1f = roi
        x0, y0 = int(max(0, min(img_w, x0f * img_w))), int(max(0, min(img_h, y0f * img_h)))
        x1, y1 = int(max(0, min(img_w, x1f * img_w))), int(max(0, min(img_h, y1f * img_h)))
        roi_mask = np.zeros_like(mask)
        roi_mask[y0:y1, x0:x1] = 1
        mask = mask * roi_mask
'''
if old not in s: raise SystemExit('target 1 not found')
s=s.replace(old,new,1)
s=s.replace('''    ap.add_argument("--save-every", type=int, default=10)
''','''    ap.add_argument("--save-every", type=int, default=10)
    ap.add_argument("--roi", default="0.35,0.55,0.85,1.0", help="normalized x0,y0,x1,y1 ROI for target search")
''')
s=s.replace('''            comp, mask = detect_white_target(bgr, args.s_max, args.v_min, args.min_area)
''','''            roi = tuple(float(x) for x in args.roi.split(",")) if args.roi else None
            comp, mask = detect_white_target(bgr, args.s_max, args.v_min, args.min_area, roi=roi)
''')
p.write_text(s)
print('patched ROI')
