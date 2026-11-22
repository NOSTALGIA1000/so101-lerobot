param(
    [string]$Distro = "LeRobot-Ubuntu-F",
    [string]$FollowerBusId = "6-4",
    [switch]$RunPreflight,
    [switch]$RunV4Probe8
)

$ErrorActionPreference = "Stop"

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdmin)) {
    $argsList = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$PSCommandPath`"",
        "-Distro", $Distro,
        "-FollowerBusId", $FollowerBusId
    )
    if ($RunPreflight) { $argsList += "-RunPreflight" }
    if ($RunV4Probe8) { $argsList += "-RunV4Probe8" }
    Start-Process -FilePath "powershell.exe" -ArgumentList $argsList -Verb RunAs -Wait
    exit $LASTEXITCODE
}

$logDir = "C:\Users\ASUS\Documents\lerobot\rollout_admin_logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$log = Join-Path $logDir "fix_wsl_usb_$stamp.log"

Start-Transcript -Path $log -Force | Out-Null
try {
    Write-Host "=== SO-101 WSL/USB recovery ==="
    Write-Host "Distro: $Distro"
    Write-Host "Follower busid: $FollowerBusId"
    Write-Host ""

    Write-Host "--- usbipd list before ---"
    usbipd list

    Write-Host "--- start WSL distro ---"
    wsl.exe -d $Distro -u nostalgia -- bash -lc "echo WSL_READY; sleep 2"

    Write-Host "--- attach follower ---"
    usbipd attach --wsl $Distro --busid $FollowerBusId

    Write-Host "--- usbipd list after attach ---"
    usbipd list

    Write-Host "--- WSL USB/dev nodes ---"
    wsl.exe -d $Distro -u nostalgia -- bash -lc "lsusb; echo ---DEV---; ls -l /dev/ttyACM* /dev/video* 2>/dev/null || true"

    Write-Host "--- chmod follower ---"
    wsl.exe -d $Distro -u root -- bash -lc "chmod 666 /dev/ttyACM0 && ls -l /dev/ttyACM0"

    if ($RunPreflight) {
        Write-Host "--- conda preflight ---"
        $preflightCmd = 'source "$HOME/miniconda3/etc/profile.d/conda.sh"; conda activate lerobot; python3 /mnt/c/Users/ASUS/Documents/lerobot/wsl/preflight_check.py'
        wsl.exe -d $Distro -u nostalgia -- bash -lc $preflightCmd

        Write-Host "--- port ID check ---"
        $matchPortsCmd = 'source "$HOME/miniconda3/etc/profile.d/conda.sh"; conda activate lerobot; python3 /mnt/c/tmp/match_ports.py'
        wsl.exe -d $Distro -u nostalgia -- bash -lc $matchPortsCmd
    }

    if ($RunV4Probe8) {
        Write-Host "--- V4 50K resfix probe8 ---"
        $v4ProbeCmd = 'export ROLLOUT_AUTO_CONFIRM=1; export ROLLOUT_DURATION=8; export ROLLOUT_LOG_SUFFIX=_resfix_probe8; bash /mnt/c/Users/ASUS/Documents/lerobot/wsl/run_v4_50k_pure.sh'
        wsl.exe -d $Distro -u nostalgia -- bash -lc $v4ProbeCmd
    }

    Write-Host ""
    Write-Host "DONE. Log: $log"
}
finally {
    Stop-Transcript | Out-Null
}
