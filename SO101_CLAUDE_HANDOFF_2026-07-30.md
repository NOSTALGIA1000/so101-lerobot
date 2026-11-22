# SO-ARM101 + LeRobot + ACT 项目交接文档

日期：2026-07-30  
接手对象：Claude / Codex / 任何后续工程 agent  
当前阶段：真机 ACT rollout 调试，训练阶段暂停

---

## 1. 项目目标

机器人：

```text
JoyandAI SO-ARM101
```

任务：

```text
cube pick and place
```

最终目标：

```text
使用 camera observation + robot state，让 ACT policy 控制 SO-ARM101：

approach cube
align gripper
grasp cube
lift cube
move cube to white target
release cube
```

当前不要重新搭真机环境。真机、遥操作、数据采集链路已经跑通过。

---

## 2. 当前工程根目录

Windows 主工作区：

```text
C:\Users\ASUS\Documents\lerobot
```

主要长期存储：

```text
F:\CC-project\lerobot-storage
```

Obsidian 记录目录：

```text
C:\Users\ASUS\Documents\Obsidian Vault\SO-ARM101\ACT Rollout Debug
```

WSL distro：

```text
LeRobot-Ubuntu-F
```

WSL 用户：

```text
nostalgia
```

WSL LeRobot 源码：

```text
/home/nostalgia/lerobot_workspace/lerobot
```

核心 rollout 文件：

```text
/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py
```

---

## 3. 当前最佳模型与 checkpoint

当前最佳 policy：

```text
ACT
```

当前最佳 checkpoint：

```text
V2 100000
```

Windows checkpoint 路径：

```text
F:\CC-project\lerobot-storage\outputs\real_test_candidates\act_v2_050000\checkpoints-V2\100000\pretrained_model
```

WSL checkpoint 路径：

```text
/mnt/f/CC-project/lerobot-storage/outputs/real_test_candidates/act_v2_050000/checkpoints-V2/100000/pretrained_model
```

重要结论：

```text
V2 70K -> V2 100K loss 继续下降，但真机表现几乎没有变化。
当前瓶颈不是训练 step 数，而是真机最后 grasp/place 的视觉闭环与动作校准。
```

---

## 4. 数据集状态

历史数据集：

| 数据集 | 状态 | 当前建议 |
|---|---|---|
| V1 | 旧数据 | 跳过 |
| V2 | 当前主力，已训到 100K | 真机最佳候选 |
| V3 | 旧/漂移 | 不作为当前主线 |
| V4 | 未优先 | 暂停 |
| V5 | 未优先 | 暂停 |
| V6 | 可与 V3 合并 | 暂停 |
| V7 | V3+V6 合并版，已测 | 当前不优先 |

当前不要继续训练，除非明确要做新数据闭环。

---

## 5. AutoDL / 云训练经验

以后如果再训练，必须遵守：

```text
ACT 默认训练参数：
batch_size = 32
steps = 100000
save_freq = 10000
```

AutoDL 原则：

```text
优先使用 AutoDL 已有 lerobot 镜像环境。
不要频繁新建 conda 环境。
如果镜像自带 lerobot-train 入口坏了，使用原生 conda env lerobot + clone 源码到 /root/autodl-tmp/lerobot + pip install -e .
数据放 /root/autodl-tmp/huggingface/lerobot 下。
```

常用云端数据路径：

```text
/root/autodl-tmp/huggingface/lerobot/so101_cube_pick_place_v2
/root/autodl-tmp/huggingface/lerobot/so101_cube_white_paper_v7
```

常用云端输出路径：

```text
/root/autodl-tmp/lerobot_outputs
```

---

## 6. 真机硬件与连接

机器人端口：

```text
follower: /dev/ttyACM0
```

相机：

```text
scene camera
wrist camera
```

ZMQ camera bridge：

```text
server_address: 172.28.48.1
port: 5555
```

当前 LeRobot rollout camera 配置：

```text
--robot.cameras="{wrist: {type: zmq, server_address: 172.28.48.1, port: 5555, camera_name: wrist, width: 64, height: 64, fps: 30}, scene: {type: zmq, server_address: 172.28.48.1, port: 5555, camera_name: scene, width: 64, height: 64, fps: 30}}"
```

rename_map：

```text
{"observation.images.scene": "observation.images.overhead"}
```

Windows camera bridge 脚本：

```text
F:\CC-project\lerobot\start_camera_bridge_two.ps1
```

最近有效启动方式：

```powershell
F:\CC-project\lerobot\start_camera_bridge_two.ps1 -Distro LeRobot-Ubuntu-F -WristIndex 1 -SceneIndex 0
```

当前相机状态经验：

```text
index0 = scene，有效看到 robot/cube/table
index1 = 非黑图，但不一定是真正 wrist close view，可能看到手机/屏幕，需要下次继续确认
```

如果 scene/wrist 图像黑：

```text
优先检查是不是抓到电脑内置摄像头/错误 index。
不要先怀疑 USB 线，用户已确认接线没问题。
```

---

## 7. WSL 命令执行注意事项

推荐 Windows PowerShell 调 WSL：

```powershell
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash -lc "命令"
```

但 PowerShell 多层引号容易炸。复杂命令推荐：

```text
1. 写成 .sh 脚本放到 C:\Users\ASUS\Documents\lerobot\wsl\
2. 用 WSL 运行：
   wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/xxx.sh
```

不要写复杂 inline bash。

---

## 8. 当前核心 rollout 脚本

基础 V2 checkpoint rollout：

```text
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_checkpoint_cube_10s_unlimited.sh
```

当前较好抓取 + fixed place macro：

```text
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_100k_cube_20s_z_p6_macro_clamp_pose45_place.sh
```

place pan 测试：

```text
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_100k_cube_20s_z_p6_macro_clamp_pose45_place_pan_p1p5.sh
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_100k_cube_20s_z_p6_macro_clamp_pose45_place_pan_p5.sh
```

elbow radial extend 测试：

```text
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_100k_cube_22s_z_p6_macro_place_elbow_extend.sh
```

空手 place pose scan：

```text
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_100k_place_pose_scene_scan.sh
```

---

## 9. 当前最佳抓取参数

当前 grasp 阶段最有效配置：

```text
ROLLOUT_GRIPPER_TIMING_GATE=open_then_close_intent
ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN=0
ROLLOUT_GRIPPER_OPEN_VALUE=45
ROLLOUT_GRIPPER_CLOSE_INTENT_MAX=10
ROLLOUT_GRIPPER_CLOSE_DELAY_HITS=3

ROLLOUT_Z_BIAS=6.0
ROLLOUT_Z_BIAS_TRIGGER=pose
ROLLOUT_Z_POSE_SHOULDER_LIFT_MIN=30
ROLLOUT_Z_POSE_ELBOW_FLEX_MAX=-47
ROLLOUT_Z_POSE_WRIST_FLEX_MIN=100
```

重要现场结论：

```text
Z bias 正方向才是更深下探。
Z +6 当前最好。
Z 负方向会更高，是错误方向。
```

---

## 10. 已知失败模式

### 10.1 原始 ACT

现象：

```text
能到 cube 附近，但最后抓取失败。
```

action log 发现：

```text
t≈0: gripper≈4
t≈8: gripper≈2
```

结论：

```text
gripper 从一开始就处于 close-like 区间。
不能用 gripper threshold 判断 grasp phase。
```

### 10.2 gripper bias

尝试：

```text
threshold=50, bias=15
```

结果：

```text
闭合过早。
```

结论：

```text
不要继续调 gripper bias。
```

### 10.3 fixed joint-space place macro

尝试过：

```text
shoulder_pan = 0
shoulder_pan = 1.5
shoulder_pan = 5
shoulder_pan = 8
elbow_flex extend
```

现象：

```text
有些动作能抓住/带起 cube，但无法稳定放到 white target。
单独调 shoulder_pan 主要表现为绕底座旋转，不等价于桌面 X/Y 平移。
```

结论：

```text
固定 joint macro 没有泛化能力。
不要继续靠固定角度猜白纸位置。
```

---

## 11. OpenCV / scene camera 研究方向

已经新增脚本：

保存原始 ZMQ camera frame：

```text
C:\Users\ASUS\Documents\lerobot\wsl\save_raw_zmq_camera_frames.py
```

white target 检测：

```text
C:\Users\ASUS\Documents\lerobot\wsl\detect_white_target_from_zmq.py
```

scene place error 检测：

```text
C:\Users\ASUS\Documents\lerobot\wsl\detect_scene_place_error_from_zmq.py
```

运行 scene place error debug：

```text
C:\Users\ASUS\Documents\lerobot\wsl\run_scene_place_error_debug.sh
```

复制最新 debug 图：

```text
C:\Users\ASUS\Documents\lerobot\wsl\copy_latest_scene_place_error_debug.sh
```

最新 debug 图：

```text
C:\Users\ASUS\Documents\lerobot\scene_place_error_latest.jpg
```

最新检测结果：

```text
frames = 73
valid_pairs = 73 / 73
mean_dx_dy ≈ [108.35, -3.23]
```

解释：

```text
white target 检测正确。
purple cube 检测正确。
当前 cube 和 white target 纵向基本对齐，主要误差是横向 dx。
```

注意：

```text
最初 generic saturated cube detector 会把蓝色桌面当成 cube。
已经改为 purple HSV detector。
```

---

## 12. 已修改 LeRobot core.py 能力

核心文件：

```text
/home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py
```

已加入/用过的环境变量能力：

```text
ROLLOUT_DEBUG_ACTION
ROLLOUT_ACTION_LOG_PATH

ROLLOUT_GRIPPER_TIMING_GATE
ROLLOUT_GRIPPER_REQUIRE_OPEN_SEEN
ROLLOUT_GRIPPER_OPEN_VALUE
ROLLOUT_GRIPPER_CLOSE_INTENT_MAX
ROLLOUT_GRIPPER_CLOSE_DELAY_HITS

ROLLOUT_Z_BIAS
ROLLOUT_Z_BIAS_TRIGGER
ROLLOUT_Z_POSE_SHOULDER_LIFT_MIN
ROLLOUT_Z_POSE_ELBOW_FLEX_MAX
ROLLOUT_Z_POSE_WRIST_FLEX_MIN

ROLLOUT_AFTER_GRASP_MACRO
ROLLOUT_FORCE_MACRO_AT_START
ROLLOUT_MACRO_SCAN_PLACE_PANS
```

---

## 13. 下一步任务：Claude 应该从这里接

不要做：

```text
不要重新训练
不要调 V2/V7 checkpoint
不要继续加 gripper bias
不要继续固定 shoulder_pan/elbow_flex 猜 place
```

应该做：

```text
实现 after-grasp scene visual servo place
```

推荐步骤：

```text
Step 1:
在 after-grasp/lift 之后，调用 scene camera OpenCV detector。

Step 2:
每帧输出：
  target_cx, target_cy
  cube_cx, cube_cy
  dx = target_cx - cube_cx
  dy = target_cy - cube_cy

Step 3:
先 dry-run logging，不控制机器人。

Step 4:
如果 dx/dy 稳定，再接小幅闭环：
  shoulder_pan += k_pan * dx
  elbow_flex += k_elbow * dy

Step 5:
加入 release 条件：
  abs(dx) < 20
  abs(dy) < 20
  stable_frames >= 10

Step 6:
release gripper。
```

建议新增脚本：

```text
C:\Users\ASUS\Documents\lerobot\wsl\run_v2_100k_scene_servo_place_debug.sh
```

建议新增环境变量：

```text
ROLLOUT_SCENE_SERVO_PLACE=1
ROLLOUT_SCENE_SERVO_DRY_RUN=1
ROLLOUT_SCENE_SERVO_TARGET=white
ROLLOUT_SCENE_SERVO_OBJECT=purple_cube
ROLLOUT_SCENE_SERVO_DX_THRESHOLD=20
ROLLOUT_SCENE_SERVO_DY_THRESHOLD=20
ROLLOUT_SCENE_SERVO_STABLE_FRAMES=10
```

---

## 14. 快速检查命令

检查 core.py 语法：

```powershell
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash -lc "python3 -m py_compile /home/nostalgia/lerobot_workspace/lerobot/src/lerobot/rollout/strategies/core.py"
```

运行 OpenCV scene debug：

```powershell
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_scene_place_error_debug.sh
```

复制最新 debug 图：

```powershell
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/copy_latest_scene_place_error_debug.sh
```

运行当前 V2 100K fixed macro baseline：

```powershell
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v2_100k_cube_22s_z_p6_macro_place_elbow_extend.sh
```

---

## 15. 当前最终判断

当前项目不是“模型完全不会”的状态。

更准确判断：

```text
ACT 已经学到了接近和抓取的主轨迹。
失败集中在真机最后几厘米的 contact/place 视觉闭环。
```

因此下一阶段正确路线是：

```text
ACT for grasp
OpenCV scene visual servo for place
```

这份文档应足够让 Claude 直接接手，不需要从头回顾聊天记录。

---

## V7 checkpoint 本机路径更新

用户已确认 V7 checkpoint 已复制回本机。

V7 主目录：

```text
F:\CC-project\lerobot-storage\outputs\real_test_candidates\act_v7_050000
```

V7 checkpoint 根目录：

```text
F:\CC-project\lerobot-storage\outputs\real_test_candidates\act_v7_050000\pretrained_model\checkpoints-V7
```

已确认存在：

```text
010000
020000
030000
040000
050000
060000
070000
080000
090000
100000
```

V7 100K Windows 路径：

```text
F:\CC-project\lerobot-storage\outputs\real_test_candidates\act_v7_050000\pretrained_model\checkpoints-V7\100000\pretrained_model
```

V7 100K WSL 路径：

```text
/mnt/f/CC-project/lerobot-storage/outputs/real_test_candidates/act_v7_050000/pretrained_model/checkpoints-V7/100000/pretrained_model
```

当前策略建议：

```text
V7 checkpoint 已可用于本机真机测试，但当前主线仍建议优先解决 scene-camera visual servo place。
不要因为 V7 已有 100K 就回到继续盲测 checkpoint。
如果要对比 V2/V7，应在同一套 OpenCV place servo 和同一 cube/target 条件下比较。
```
