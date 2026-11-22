import cv2, numpy as np, os, glob
d = '/home/nostalgia/lerobot_outputs/rollouts/scene_place_error_debug_20260730'
imgs = sorted(glob.glob(os.path.join(d, '*_scene_place_error.jpg')))
if not imgs:
    print('No images')
    exit(1)
img = cv2.imread(imgs[0])
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Test: exact same pipeline as detect_cube_candidate
h, s, v = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]
raw = (h >= 120) & (h <= 170) & (s >= 50) & (v >= 60)
print(f'Raw px: {raw.sum()}')

mask = raw.astype(np.uint8)
# ROI (default cube roi: 0.05,0.30,0.95,0.95)
h_img, w_img = hsv.shape[:2]
x0, y0 = int(0.05*w_img), int(0.30*h_img)
x1, y1 = int(0.95*w_img), int(0.95*h_img)
roi = np.zeros_like(mask)
roi[y0:y1, x0:x1] = 1
mask = mask * roi
print(f'After ROI: {mask.sum()}')

# clean_mask with kernel=3
k3 = np.ones((3,3), np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k3)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k3)
print(f'After morph(k=3): {mask.sum()}')

# largest_component min_area=80
n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
print(f'Components: {n-1}')
for i in range(1, min(n, 10)):
    area = int(stats[i, cv2.CC_STAT_AREA])
    print(f'  C{i}: area={area}')
