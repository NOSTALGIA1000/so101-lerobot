param(
    [ValidateSet(1,2,3,4)]
    [int]$Level = 1,
    [string]$Distro = "LeRobot-Ubuntu-F",
    [int]$TimeoutSeconds = 20,
    [switch]$Apply
)

$ErrorActionPreference = "Continue"

$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

function Write-Step {
    param([string]$Message)
    Write-Host ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Message)
}

function Invoke-Maybe {
    param(
        [string]$Description,
        [scriptblock]$Action
    )

    if ($Apply) {
        Write-Step ("APPLY: {0}" -f $Description)
        & $Action
    } else {
        Write-Step ("DRY-RUN: {0}" -f $Description)
    }
}

function Invoke-ProcessWithTimeout {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [int]$Timeout = $TimeoutSeconds
    )

    $outFile = Join-Path $env:TEMP ("wsl_repair_out_{0}.txt" -f ([guid]::NewGuid()))
    $errFile = Join-Path $env:TEMP ("wsl_repair_err_{0}.txt" -f ([guid]::NewGuid()))
    try {
        $p = Start-Process -FilePath $FilePath -ArgumentList $Arguments -NoNewWindow -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
        if (-not $p.WaitForExit($Timeout * 1000)) {
            Write-Step ("TIMEOUT: {0} {1}" -f $FilePath, ($Arguments -join " "))
            try { $p.Kill() } catch {}
            return 124
        }
        Get-Content -LiteralPath $outFile -ErrorAction SilentlyContinue
        Get-Content -LiteralPath $errFile -ErrorAction SilentlyContinue
        return $p.ExitCode
    } finally {
        Remove-Item -LiteralPath $outFile,$errFile -Force -ErrorAction SilentlyContinue
    }
}

function Stop-ClientProcesses {
    $names = "wsl","wslhost","taskkill"
    $procs = Get-Process $names -ErrorAction SilentlyContinue
    if (-not $procs) {
        Write-Step "No stale wsl/wslhost/taskkill client processes found."
        return
    }

    $procs | Select-Object ProcessName,Id,StartTime | Format-Table -AutoSize
    Invoke-Maybe "Stop stale client processes: $($procs.Id -join ', ')" {
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-WslShutdown {
    Invoke-Maybe "Run wsl.exe --shutdown to clear the half-started WSL VM" {
        $exitCode = Invoke-ProcessWithTimeout -FilePath "wsl.exe" -Arguments @("--shutdown") -Timeout $TimeoutSeconds
        if ($exitCode -eq 124) {
            Write-Step "wsl --shutdown timed out. Falling back to force-stopping vmwp/vmmemWSL."
            Get-Process vmmemWSL,vmwp -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        }
    }
}

function Restart-OptionalService {
    param([string]$Name)

    $svc = Get-Service $Name -ErrorAction SilentlyContinue
    if (-not $svc) {
        Write-Step "Service not present: $Name"
        return
    }

    Invoke-Maybe "Restart service $Name (current status: $($svc.Status))" {
        try {
            Restart-Service -Name $Name -Force -ErrorAction Stop
        } catch {
            Write-Step ("Restart-Service failed for {0}: {1}" -f $Name, $_.Exception.Message)
        }
    }
}

function Test-WslAfterRepair {
    Write-Step "Testing WSL management command."
    [void](Invoke-ProcessWithTimeout -FilePath "wsl.exe" -Arguments @("-l","-v") -Timeout $TimeoutSeconds)

    Write-Step "Testing minimal distro startup."
    [void](Invoke-ProcessWithTimeout -FilePath "wsl.exe" -Arguments @("-d",$Distro,"-u","root","--","bash","-lc","echo WSL_OK; date") -Timeout $TimeoutSeconds)
}

Write-Step "WSL repair requested. Level=$Level Distro=$Distro Apply=$Apply"
Write-Step "Without -Apply this script only prints intended actions."
Write-Step "RunningAsAdministrator=$IsAdmin"
if ($Apply -and $Level -ge 2 -and -not $IsAdmin) {
    Write-Step "WARNING: Level 2 service restart usually requires an elevated Administrator PowerShell."
}

if ($Level -ge 1) {
    Write-Step "Level 1: clear stale client processes and shut down WSL VM."
    Stop-ClientProcesses
    Invoke-WslShutdown
}

if ($Level -ge 2) {
    Write-Step "Level 2: refresh WSL-adjacent Windows services."
    Restart-OptionalService -Name "LxssManager"
    Restart-OptionalService -Name "vmcompute"
    Restart-OptionalService -Name "hns"
}

if ($Level -ge 3) {
    Write-Step "Level 3: Linux startup inspection. This does not edit Linux files."
    Invoke-Maybe "Run Linux startup inspection commands through WSL" {
        [void](Invoke-ProcessWithTimeout -FilePath "wsl.exe" -Arguments @("-d",$Distro,"-u","root","--","bash","-lc","systemd-analyze blame --no-pager | head -80; systemd-analyze critical-chain --no-pager; journalctl -b -p warning --no-pager | tail -120; cat /etc/fstab") -Timeout 60)
    }
}

if ($Level -ge 4) {
    Write-Step "Level 4 is not automated. Export the distro before unregister/import."
    Write-Step ("Backup command: wsl --export {0} C:\tmp\{0}_backup.tar" -f $Distro)
    Write-Step "Only proceed manually after verifying the backup tar exists and can be listed."
}

if ($Apply -and $Level -le 3) {
    Test-WslAfterRepair
}

Write-Step "Repair procedure finished."
