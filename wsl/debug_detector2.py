"""Debug with conda lerobot env python."""
import cv2, numpy as np, os, glob, sys
print(f'Python: {sys.executable}')
print(f'OpenCV: {cv2.__version__}')
d = '/home/nostalgia/lerobot_outputs/rollouts/scene_place_error_debug_20260730'
imgs = sorted(glob.glob(os.path.join(d, '*_scene_place_error.jpg')))
print(f'Images: {len(imgs)}')
if not imgs:
    exit(1)
img = cv2.imread(imgs[0])
if img is None:
    print(f'Cannot read {imgs[0]}')
    exit(1)
print(f'Shape: {img.shape}, mean={img.mean():.0f}')
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
print(f'H range: [{hsv[:,:,0].min()}-{hsv[:,:,0].max()}]')
print(f'S range: [{hsv[:,:,1].min()}-{hsv[:,:,1].max()}]')
print(f'V range: [{hsv[:,:,2].min()}-{hsv[:,:,2].max()}]')

# Test purple detection
h, s, v = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]
for smin, vmin in [(70, 60), (50, 60), (40, 50), (30, 40)]:
    raw = (h >= 120) & (h <= 170) & (s >= smin) & (v >= vmin)
    print(f'H[120,170] S>={smin} V>={vmin}: {raw.sum()} px')
