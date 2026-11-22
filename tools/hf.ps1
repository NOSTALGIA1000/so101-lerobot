$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$HfCliPath = Join-Path $RepoRoot ".hf_cli"
$HfExe = Join-Path $HfCliPath "bin\hf.exe"
$ProjectHfHome = Join-Path $RepoRoot ".hf_cache"

if (-not (Test-Path -LiteralPath $HfExe)) {
    throw "Project-local Hugging Face CLI executable not found: $HfExe"
}

$env:PYTHONPATH = if ($env:PYTHONPATH) {
    "$HfCliPath;$env:PYTHONPATH"
} else {
    $HfCliPath
}

if (-not $env:HF_HOME) {
    $env:HF_HOME = $ProjectHfHome
}

if (-not $env:HF_HUB_DISABLE_SYMLINKS_WARNING) {
    $env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
}

if (-not $env:HTTP_PROXY) {
    $env:HTTP_PROXY = "http://127.0.0.1:10808"
}

if (-not $env:HTTPS_PROXY) {
    $env:HTTPS_PROXY = "http://127.0.0.1:10808"
}

& $HfExe @args
exit $LASTEXITCODE
