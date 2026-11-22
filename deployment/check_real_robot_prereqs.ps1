param(
    [string]$Distro = "LeRobot-Ubuntu-F",
    [string]$FollowerPort = "/dev/ttyACM0"
)

$ErrorActionPreference = "Stop"

Write-Host "== Windows process sanity =="
$taskkillCount = @(Get-Process taskkill -ErrorAction SilentlyContinue).Count
$pythonCount = @(Get-Process python,pythonw -ErrorAction SilentlyContinue).Count
Write-Host "taskkill_count=$taskkillCount"
Write-Host "python_count=$pythonCount"

Write-Host "== WSL distro list =="
wsl.exe -l -v

Write-Host "== WSL echo check =="
wsl.exe -d $Distro -u nostalgia -- bash -lc "echo WSL_OK && uname -a"

Write-Host "== Follower read-only check command =="
Write-Host "Run only when follower USB and power are ready:"
Write-Host "wsl.exe -d $Distro -u nostalgia -- bash -lc `"source ~/miniconda3/etc/profile.d/conda.sh && conda activate lerobot && python /mnt/c/Users/ASUS/Documents/lerobot/wsl/check_follower_readonly.py --port $FollowerPort`""

Write-Host "== Policy status =="
Get-Content "$PSScriptRoot\policy_registry.json"
