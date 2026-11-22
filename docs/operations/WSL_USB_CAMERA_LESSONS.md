# WSL / USB / 相机 / 舵机故障经验

整理日期：2026-11-22。来源：本对话历史和仓库脚本；本次未做现场复测。

## WSL 卡死与资源配置

曾出现 `wsl.exe`、terminate/shutdown 超时、残留 `vmmemWSL`、usbipd TCP 10060，以及 CH343 从 Attached 回到 Shared。这些是症状，不能单凭它们认定共享内存不足或 USB 驱动损坏。

历史主机约 16GB RAM，采用以下资源上限：

```ini
[wsl2]
memory=10GB
processors=6
swap=8GB
```

[共享内存脚本](../../wsl/apply_wsl_stability_fixes.sh)将 `/dev/shm` 上限设为 6G，并备份 `/etc/fstab`。tmpfs 上限不是新增物理内存，也不是预分配 6G；实际使用仍消耗 WSL 资源。应结合可用内存、swap、OOM/内核日志和 Windows 负载判断，不能把扩大 shm 当作所有卡死问题的修复。

[7 月 23 日报告](../../F-CCproject/codex-project/wsl-startup-recovery/ROOT_CAUSE_REPORT_20260723.md)记录了管理员刷新宿主机网络/计算服务后恢复。它支持宿主服务/连接状态异常的解释，不能排除所有其他原因；报告中的百分比置信度不是统计测量。

恢复顺序：

1. 停止真机动作，托稳机械臂并断舵机电源；暂停 attach、相机与训练重试。
2. 带超时做一次最小 WSL 检查；保存症状及 Windows/WSL 日志，避免堆积新的客户端进程。
3. 优先正常关闭 WSL；无响应时按已有恢复脚本在管理员窗口处理。会中断所有相关 Linux 工作，先确认没有需保留的任务。
4. 若管理服务和 VM 仍卡住，保存 Windows 工作后重启。不要循环强杀整个 `vmwp` 或其他共享虚拟化进程。
5. 连续三次 `WSL_OK` 正常返回后再恢复 USB。这只是基础响应验收，不是训练稳定性证明。

```powershell
wsl -d LeRobot-Ubuntu-F -u nostalgia -- bash -lc "echo WSL_OK"
```

应在外层设等待上限，历史目标为热启动 10 秒内返回。默认 `wsl -e bash` 可能进入另一发行版，看到 `asus` 用户不能证明正式环境已恢复。

## USB 占用和枚举

- VirtualBox 曾占用 CH343；关闭 VM 后恢复是本项目的重要经验。串口只应由一个环境拥有。关闭虚拟机并检查其 USB 过滤器，不必卸载 VirtualBox。
- `usbipd list` 显示 Shared 只表示已共享，不表示已接入 WSL。Attached 后仍需在目标发行版验证设备节点和电机应答。
- BUSID、COM 编号、`ttyACM` 编号会变化。历史 follower 从 Windows 拔出后，`2-1 / COM5` 消失，另一块 `6-1 / COM6` 留下；后来 follower 为 `6-4`。这些都不是永久标识。
- 用当前 USB 列表、`/dev/serial/by-id`（存在时）、插拔差异和设备序列号核对，不凭 `/dev/ttyACM0` 就认定 follower。
- USB 提示音只说明 Windows 检测到插拔，不代表驱动、WSL 接入、供电和电机通信全部正常。
- 拓展坞的 Type-C 上行插电脑，设备接下行 USB；核对数据传输能力与供电。舵机按铭牌使用正确外部电源，不能假设 USB 能给舵机供电。
- 曾出现 `PNP_DETECTED` 蓝屏与 `hrdevmon` 过滤器警告；没有本次可复核的根因证据，不能断言某个驱动就是原因，也不应默认使用 `bind --force`。

```powershell
usbipd list
# 仅在已确认实际 follower BUSID、WSL 响应且设备已共享后执行：
usbipd attach --wsl LeRobot-Ubuntu-F --busid <当前follower-BUSID>
```

初次 bind 需要管理员权限；普通 PowerShell 中调用带 `#requires -RunAsAdministrator` 的脚本不会自动提权。历史 winget 安装曾报 1619，随后 usbipd 可用，但没有足够证据记录具体修复原因。

Linux 权限先检查 `ls -l`、用户组和占用进程；历史 `chmod 666` 是临时措施且放宽所有本地用户访问，长期使用串口组或针对设备的 udev 规则。设备节点不存在时 chmod 无法解决问题。

## 相机映射与模型输入

| 阶段 | 历史记录 | 复用限制 |
| --- | --- | --- |
| 本对话 V1 | wrist=index 0，scene=index 1；index 2 曾是错误墙面视角 | 640×480，模型键 wrist/scene |
| 仓库 7 月 30 日记录 | scene=index 0；index 1 的 wrist 视角仍待确认 | 后续脚本含 64×64 和 scene→overhead rename，不能用于 V1 原样复用 |

每次启动保存两路样张，核对镜头、物体、分辨率、颜色通道和帧新鲜度。图像非黑只是最低检查；遮挡或夹爪挡住画面也会影响模型，不能因“能收到”就放行。

[check_camera_bridge.py](../../wsl/check_camera_bridge.py)硬编码历史地址 `172.28.48.1:5555`；先核对当前 Windows 可达地址。接收 shape 成功并不测量稳定 30 FPS、时延或同步，需要另行记录。

NAT 模式的 localhost 代理警告针对网络代理可达性，不等同于 WSL 崩溃。桥接网络也不保证所有下载都不需要代理。

## 真机测试顺序

1. 关闭占用 USB 的 VM；WSL 响应通过后，确认并 attach follower。自主推理不依赖 leader；遥操作采集才需要它。
2. 核对串口身份、权限和占用，再运行 [follower 只读检查](../../wsl/check_follower_readonly.py)，要求 IDs 1–6 返回位置，标定文件匹配 `R12260101`。
3. 核对相机实拍画面、模型输入键及预处理；离线推理和频率检查通过后再上机。
4. 清空运动区，操作者可立即断电。从短轮次开始。V1 曾用 0.5、5–8 秒起测，后用 1.0、8–10 秒；必须核对当前动作单位，数值不是跨模型安全保证。
5. WSL 超时、USB 掉线、总线读失败、异常抖动/偏移或持续大量限幅即停止；原计划目标 ≥25Hz，低于 10Hz 属明确停止条件，10–25Hz 也未达到验收要求。
6. 测后检查串口仍应答、WSL 仍响应、rollout 已退出，再记录夹持/抬离/保持 3 秒、碰撞、频率和异常。

[rollout_act_cube_safe.sh](../../wsl/rollout_act_cube_safe.sh)默认实际为 1.5、15 秒，不能误以为脚本名保证了上述短测设置。使用时必须显式传入已评审的限幅和时长。

## Leader 无电机应答

历史现象：`/dev/ttyACM1` 存在，IDs 1–6 全部缺失。节点存在只证明串口被枚举，不证明电机供电或总线通。

依次检查端口身份、串口占用、VM/WSL 归属、正确电压供电、三针总线方向和连接、实际波特率与 ID。优先使用安装版本的 LeRobot 总线读取/扫描接口。原始手写串口扫描器需验证报文长度、校验和与响应解析，不能把其超时直接当成硬件坏了。

没有确认通信前，不重新编号、写 ID 或重标定。保留现有 follower 标定；不要把 leader 故障处理扩展到另一只臂。

## 师弟的白色机械臂四号舵机问题（独立案例，未确诊）

用户转述：最初数天正常，后来四号通信失败，断电扭动阻力明显偏大。这不是本机故障，也没有维修完成证据。

建议：托稳机械臂，断电及 USB，确认舵机完全断电；检查支架干涉、限位、线材和插头。所有换线在断电时操作，用已知正常且规格匹配的线/供电单独测试四号，只读扫描。若同一接法其他舵机应答、四号不应答，故障更集中于四号本体；若排除外部干涉后仍卡涩，联系售后。不要硬掰或反复带故障运动。

先前正常不能完全排除端口重枚举或配置变化，但单独四号失败并伴随异常机械阻力，应优先检查线材与本体；重新标定不能修复通信中断或机械卡滞。未验证前不写“已烧毁”。
