param(
    [int]$MaxIndex = 6,
    [string]$OutDir = "C:\Users\ASUS\Documents\lerobot\camera_probe_live"
)

$ErrorActionPreference = "Stop"

$python = "F:\CC-project\lerobot\.camera-bridge-venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Camera bridge Python not found: $python"
}

$script = Join-Path $PSScriptRoot "probe_windows_cameras.py"
& $python $script --max-index $MaxIndex --out-dir $OutDir
