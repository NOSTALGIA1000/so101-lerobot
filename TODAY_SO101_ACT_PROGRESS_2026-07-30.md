# 2026-07-30 SO-ARM101 ACT rollout progress

## 今日最终状态

今天任务停止在：

```text
V2 100K ACT 真机 rollout 已能完成接近 cube、下探、闭合、部分抓起/带起 cube。
但固定 joint-space place macro 仍未能稳定把 cube 放到 white target。
```

当前结论：

```text
不要继续靠固定 joint angle 猜 place。
不要继续训练 V2/V7。
不要继续调 gripper bias。
下一阶段改为 scene-camera OpenCV visual servo place。
```

## 当前最佳抓取配置

```text
Policy: ACT
Checkpoint: V2 100000
Z bias: +6.0
Gripper gate: open_then_close_intent
Open value: 45
Close intent max: 10
Close delay hits: 3
```

Checkpoint 路径：

```text
F:\CC-project\lerobot-storage\outputs\real_test_candidates\act_v2_050000\checkpoints-V2\100000\pretrained_model
/mnt/f/CC-project/lerobot-storage/outputs/real_test_candidates/act_v2_050000/checkpoints-V2/100000/pretrained_model
```

## 今天跑过的关键 rollout 脚本

```text
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_checkpoint_cube_10s_unlimited.sh
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_100k_cube_20s_z_p6_macro_clamp_pose45_place.sh
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_100k_cube_20s_z_p6_macro_clamp_pose45_place_pan_p1p5.sh
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_100k_cube_20s_z_p6_macro_clamp_pose45_place_pan_p5.sh
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_100k_cube_22s_z_p6_macro_place_elbow_extend.sh
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_100k_place_pose_scene_scan.sh
```

## 今天新增的 OpenCV / scene camera 脚本

```text
C:\Users\ASUS\Documents\lerobot\wsl\save_raw_zmq_camera_frames.py
C:\Users\ASUS\Documents\lerobot\wsl\detect_white_target_from_zmq.py
C:\Users\ASUS\Documents\lerobot\wsl\detect_scene_place_error_from_zmq.py
C:\Users\ASUS\Documents\lerobot\wsl\run_scene_place_error_debug.sh
C:\Users\ASUS\Documents\lerobot\wsl\copy_latest_scene_place_error_debug.sh
```

最新 debug 图：

```text
C:\Users\ASUS\Documents\lerobot\scene_place_error_latest.jpg
```

## 最新 OpenCV 检测结果

```text
frames = 73
valid_pairs = 73 / 73
mean_dx_dy ≈ [108.35, -3.23]
```

解释：

```text
white target 检测正确。
purple cube 检测正确。
当前主要误差是横向 dx，dy 基本对齐。
```

## 已修改的核心源码

```text
/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py
```

已加入能力：

```text
ROLLOUT_DEBUG_ACTION
ROLLOUT_ACTION_LOG_PATH
ROLLOUT_GRIPPER_TIMING_GATE
ROLLOUT_Z_BIAS
ROLLOUT_AFTER_GRASP_MACRO
ROLLOUT_FORCE_MACRO_AT_START
ROLLOUT_MACRO_SCAN_PLACE_PANS
```

## 关键现场结论

1. ACT V2 100K 的 grasp/lift 能力已经接近可用。
2. 训练 step 增加没有明显改善 place 阶段。
3. gripper 原始输出一直接近 close，不能用 gripper threshold 判断 grasp phase。
4. Z bias 的正确方向是正向，`+6` 当前最好。
5. fixed joint macro 可以执行，但无法泛化到 white target。
6. 单独调 shoulder_pan 会出现旋转，不等价于桌面坐标 X/Y 平移。
7. scene camera OpenCV 能稳定检测 white target 和 purple cube，具备做 place visual servo 的基础。

## 下一次继续时的第一任务

不要从训练开始。不要重新调 gripper。

下一步从这里开始：

```text
实现 after-grasp scene visual servo place：

1. ACT 执行 approach/grasp/lift
2. after-grasp phase 暂停 ACT place macro
3. scene camera 检测 cube center 和 white target center
4. 根据 dx/dy 做小幅 joint correction
5. dx/dy 稳定进入阈值后 release
```

建议先只做 logging + dry-run correction，不立即闭环控制真机。

## 推荐下一步文件

新增：

```text
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_100k_scene_servo_place_debug.sh
```

修改：

```text
/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py
```

目标环境变量：

```text
ROLLOUT_SCENE_SERVO_PLACE=1
ROLLOUT_SCENE_SERVO_DRY_RUN=1
ROLLOUT_SCENE_SERVO_TARGET=white
ROLLOUT_SCENE_SERVO_OBJECT=purple_cube
ROLLOUT_SCENE_SERVO_DX_THRESHOLD=20
ROLLOUT_SCENE_SERVO_DY_THRESHOLD=20
ROLLOUT_SCENE_SERVO_STABLE_FRAMES=10
```
