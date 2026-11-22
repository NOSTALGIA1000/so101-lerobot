"""Simulate core.py purple cube detection pipeline step by step."""
import cv2, numpy as np, os

d = '/home/nostalgia/lerobot_outputs/rollouts/scene_place_error_debug_20260730'
img = cv2.imread(os.path.join(d, '0000_scene_place_error.jpg'))
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Raw filter
raw = (hsv[:,:,0] >= 125) & (hsv[:,:,0] <= 165) & (hsv[:,:,1] >= 70) & (hsv[:,:,2] >= 60)
print(f'Raw filter (H125-165,S>=70,V>=60): {raw.sum()} px')

# Apply ROI
h_img, w_img = hsv.shape[:2]
mask = raw.astype(np.uint8)
cx0, cy0 = int(0.05*w_img), int(0.30*h_img)
cx1, cy1 = int(0.95*w_img), int(0.95*h_img)
roi = np.zeros_like(mask)
roi[cy0:cy1, cx0:cx1] = 1
mask = mask * roi
print(f'After ROI: {mask.sum()} px')

# Morph
k3 = np.ones((3,3), np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k3)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k3)
print(f'After morph: {mask.sum()} px')

# Connected components
n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
print(f'Components (excl bg): {n-1}')
for i in range(1, min(n, 15)):
    area = int(stats[i, cv2.CC_STAT_AREA])
    cx, cy = centroids[i][0], centroids[i][1]
    valid = 'PASS' if 80 <= area <= 12000 else 'FAIL'
    print(f'  C{i}: area={area}, center=({cx:.0f},{cy:.0f}), {valid}')

if n == 1:
    print('  NO COMPONENTS FOUND — cube detection fails')
    # Try without ROI
    mask2 = raw.astype(np.uint8)
    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, k3)
    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, k3)
    n2, _, stats2, centroids2 = cv2.connectedComponentsWithStats(mask2, 8)
    print(f'\nWithout ROI: {n2-1} components')
    for i in range(1, min(n2, 10)):
        area = int(stats2[i, cv2.CC_STAT_AREA])
        valid = 'PASS' if 80 <= area <= 12000 else 'FAIL'
        print(f'  C{i}: area={area}, center=({centroids2[i][0]:.0f},{centroids2[i][1]:.0f}), {valid}')
