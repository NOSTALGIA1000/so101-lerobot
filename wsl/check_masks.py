import cv2, os, glob
d = '/home/nostalgia/lerobot_outputs/rollouts/scene_place_error_debug_20260730'
cube_masks = sorted(glob.glob(os.path.join(d, '*_scene_cube_mask.png')))
target_masks = sorted(glob.glob(os.path.join(d, '*_scene_target_mask.png')))
print(f'Cube mask files: {len(cube_masks)}')
print(f'Target mask files: {len(target_masks)}')
if cube_masks:
    cm = cv2.imread(cube_masks[0], 0)
    print(f'Cube mask px: {cm.sum()/255:.0f}')
if target_masks:
    tm = cv2.imread(target_masks[0], 0)
    print(f'Target mask px: {tm.sum()/255:.0f}')
