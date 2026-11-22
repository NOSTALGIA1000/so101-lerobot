# SO-ARM101 / LeRobot 实验仓库

包含脚本、文档、仿真资产及真机实验经验。原始数据集、模型权重、运行日志、机器标定和凭据未纳入 Git；本仓库不是全部实验文件的完整备份。

## 阅读入口

- [本对话补充：V1 数据、训练与真机结果](docs/history/ACT_CUBE_V1_20260721_22.md)
- [WSL、USB、相机和舵机排查经验](docs/operations/WSL_USB_CAMERA_LESSONS.md)
- [V1 数据集元信息快照](docs/data/act_cube_v1_manifest.json)（2026-11-22 从本地 `meta/info.json` 核对；不包含视频）
- [2026-07-30 项目进展](TODAY_SO101_ACT_PROGRESS_2026-07-30.md)
- [V2/V7 工程交接](SO101_CLAUDE_HANDOFF_2026-07-30.md)
- [WSL 启动诊断历史报告](F-CCproject/codex-project/wsl-startup-recovery/ROOT_CAUSE_REPORT_20260723.md)
- [仿真策略真机门槛](deployment/REAL_ROBOT_TEST_GATE.md)（针对该文档的仿真基线，不代表所有 ACT 模型）

## 使用边界

历史配置不是当前硬件探测结果。每次重插或重启后重新确认串口、USB BUSID、相机实拍视角、WSL 地址和模型输入。V1 的 `wrist/scene`、640×480 配置不能直接替换 V2/V7 的输入配置。脚本中含实验性动作与不限幅尝试，不能仅凭文件名直接上机。

2026-11-22 本次仅补充知识文档和数据元信息，未启动 WSL、训练、USB 接入或机械臂动作；未重新验收真机性能。
