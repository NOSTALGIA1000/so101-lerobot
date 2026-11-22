"""Find working HSV params for purple cube in current lighting."""
import cv2, numpy as np, os

d = '/home/nostalgia/lerobot_outputs/rollouts/scene_place_error_debug_20260730'
img = cv2.imread(os.path.join(d, '0000_scene_place_error.jpg'))
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

for s_min in [40, 50, 60]:
    for v_min in [40, 50, 60]:
        raw = (hsv[:,:,0] >= 120) & (hsv[:,:,0] <= 170) & (hsv[:,:,1] >= s_min) & (hsv[:,:,2] >= v_min)
        mask = raw.astype(np.uint8)
        # ROI
        h_img, w_img = hsv.shape[:2]
        cx0, cy0 = int(0.05*w_img), int(0.30*h_img)
        cx1, cy1 = int(0.95*w_img), int(0.95*h_img)
        roi = np.zeros_like(mask)
        roi[cy0:cy1, cx0:cx1] = 1
        mask = mask * roi
        # Lighter morph
        k2 = np.ones((2,2), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k2)
        n, _, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
        max_area = 0
        best_cx = best_cy = 0
        for i in range(1, n):
            area = int(stats[i, cv2.CC_STAT_AREA])
            if area > max_area:
                max_area = area
                best_cx, best_cy = centroids[i][0], centroids[i][1]
        status = 'OK' if max_area >= 50 else 'TOO_SMALL'
        print(f'S>={s_min} V>={v_min}: raw={raw.sum():5d} after_morph={mask.sum():4d} max_cluster={max_area:5d} @ ({best_cx:5.0f},{best_cy:5.0f}) [{status}]')
