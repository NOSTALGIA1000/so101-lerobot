$ErrorActionPreference = "Continue"

$outDir = "C:\Users\ASUS\Documents\lerobot\rollout_analysis"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outFile = Join-Path $outDir "current_follower_state.txt"

$cmd = 'source /home/nostalgia/miniconda3/etc/profile.d/conda.sh; conda activate lerobot; python3 /mnt/c/Users/ASUS/Documents/lerobot/wsl/check_follower_readonly.py --port /dev/ttyACM0'

$output = & wsl.exe -d LeRobot-Ubuntu-F -u nostalgia -- bash -lc $cmd 2>&1
$exitCode = $LASTEXITCODE
$output | Tee-Object -FilePath $outFile
"exit_code=$exitCode" | Tee-Object -FilePath $outFile -Append

Write-Host ""
Write-Host "Wrote: $outFile"
