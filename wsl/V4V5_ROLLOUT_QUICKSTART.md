# SO-101 V4/V5 Rollout Quickstart

Use this with `C:\tmp\codex_v4v5_rollout_prompt.md`.

## Preflight

Run on Windows first:

```powershell
F:\CC-project\lerobot\start_camera_bridge_two.ps1 -Distro LeRobot-Ubuntu-F -WristIndex 1 -SceneIndex 0
usbipd attach --wsl LeRobot-Ubuntu-F --busid 6-4
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- sudo chmod 666 /dev/ttyACM0
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- python3 /mnt/c/tmp/match_ports.py
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- python3 /mnt/c/Users/ASUS/Documents/lerobot/wsl/preflight_check.py
```

Expected port identity:

```text
follower=/dev/ttyACM0 R12260101
leader=/dev/ttyACM1 R07260101
```

## First-Contact Probes

Run one short probe per model before any 15s trial:

```powershell
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v4_50k_probe8.sh
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v5_50k_probe8.sh
```

## Phase A

For each trial, reset the scene, capture before frames, run rollout, then capture after frames.

```powershell
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/capture_v4v5_trial_frames.sh v4 050000 1 before
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v4_50k_pure.sh
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/capture_v4v5_trial_frames.sh v4 050000 1 after
```

Repeat trials 1-3 for V4, then V5.

```powershell
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v5_50k_pure.sh
```

## Phase B

Only run if 50K motion is reasonable:

```powershell
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v4v5_checkpoint.sh v4 030000
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v4v5_checkpoint.sh v4 010000
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v4v5_checkpoint.sh v5 030000
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v4v5_checkpoint.sh v5 010000
```

## Record

Fill:

```text
C:\Users\ASUS\Documents\lerobot\wsl\v4v5_test_results.csv
```

Output folders in WSL:

```text
~/lerobot_outputs/rollouts/
~/lerobot_outputs/rollouts/frames/
```
