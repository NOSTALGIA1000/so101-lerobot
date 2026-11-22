$ErrorActionPreference = "Stop"
$outDir = "C:\Users\ASUS\Documents\lerobot\rollout_analysis"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $outDir "v4_mrt3_probe6_export_$stamp.txt"
$cmd = @'
set -e
LOG=/home/nostalgia/lerobot_outputs/rollouts/v4_050000_pure_mrt3_probe6.log
CSV=/home/nostalgia/lerobot_outputs/rollouts/v4_050000_pure_mrt3_probe6.csv
echo "=== FILES ==="
ls -l "$LOG" "$CSV"
echo
echo "=== LOG KEY LINES ==="
grep -aE "max_rel|max_relative|clamped|safe goal_pos|gripper|Duration limit|ERROR|Traceback|Rollout finished|disconnected" "$LOG" | tail -220 || true
echo
echo "=== LOG TAIL ==="
tail -180 "$LOG"
echo
echo "=== CSV SUMMARY ==="
source /home/nostalgia/miniconda3/etc/profile.d/conda.sh
conda activate lerobot
python3 /mnt/c/Users/ASUS/Documents/lerobot/wsl/summarize_rollout_action_csv.py "$CSV"
echo
echo "=== CSV HEAD ==="
head -8 "$CSV"
echo
echo "=== CSV TAIL ==="
tail -8 "$CSV"
'@
wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash -lc $cmd 2>&1 | Tee-Object -FilePath $out
Write-Host "WROTE $out"
