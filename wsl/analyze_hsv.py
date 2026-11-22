"""Check purple cube HSV values in latest debug frame."""
import cv2, numpy as np, os, glob

d = '/home/nostalgia/lerobot_outputs/rollouts/scene_place_error_debug_20260730'
files = sorted(glob.glob(os.path.join(d, '*_scene_place_error.jpg')))
if not files:
    print('No debug frames found')
    exit(1)

img = cv2.imread(files[0])
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
h, s, v = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]

print(f'Image: {files[0]}')
print(f'Shape: {img.shape}')

# Current purple detector
purple = (h >= 125) & (h <= 165) & (s >= 70) & (v >= 60)
print(f'\nCurrent filter (H125-165, S>=70, V>=60): {purple.sum()} px')

# Scan relaxed ranges
print('\nRelaxed range scan (>100px hits):')
for hl, hh in [(110,175), (115,170), (120,165)]:
    for smin in [30, 40, 50, 60]:
        for vmin in [30, 40, 50, 60]:
            m = (h >= hl) & (h <= hh) & (s >= smin) & (v >= vmin)
            if m.sum() > 100:
                print(f'  H[{hl},{hh}] S>={smin} V>={vmin}: {m.sum()} px')

# ROI stats
roi_h = hsv[int(0.3*h):int(0.9*h), int(0.1*img.shape[1]):int(0.9*img.shape[1])]
roi_s = hsv[int(0.3*h):int(0.9*h), int(0.1*img.shape[1]):int(0.9*img.shape[1])]
print(f'\nROI H range: [{hsv[:,:,0].min()}-{hsv[:,:,0].max()}]')
print(f'ROI S range: [{hsv[:,:,1].min()}-{hsv[:,:,1].max()}]')
print(f'ROI V range: [{hsv[:,:,2].min()}-{hsv[:,:,2].max()}]')

# Top 10 H values
unique_h, counts = np.unique(hsv[int(0.3*h):int(0.9*h), int(0.1*img.shape[1]):int(0.9*img.shape[1]), 0], return_counts=True)
top = sorted(zip(counts, unique_h), reverse=True)[:10]
print(f'\nTop 10 H values (count, H): {[(int(c), int(hv)) for c, hv in top]}')

# Check if any area has high-S purple candidates
for vmin in [30, 40, 50]:
    m = (hsv[:,:,0] >= 120) & (hsv[:,:,0] <= 170) & (hsv[:,:,1] >= 50) & (hsv[:,:,2] >= vmin)
    cnt = m.sum()
    if cnt > 0:
        # Get bounding box of largest cluster
        labels, n = cv2.connectedComponents(m.astype(np.uint8), 8)[:2]
        if n > 1:
            areas = [(labels == i).sum() for i in range(1, n)]
            print(f'\nV>={vmin}: {cnt} px, {n-1} clusters, max_area={max(areas)}')
