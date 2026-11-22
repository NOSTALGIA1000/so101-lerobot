param(
    [string]$Distro = "LeRobot-Ubuntu-F",
    [string]$User = "nostalgia",
    [string]$FollowerBusId = "6-4",
    [string]$FollowerSerial = "5AE6056685",
    [int]$CheckIntervalSeconds = 10,
    [switch]$Once
)

$ErrorActionPreference = "Continue"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $Message"
}

function Invoke-ExeWithTimeout {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [Parameter(Mandatory=$true)][string[]]$Arguments,
        [int]$TimeoutSeconds = 8
    )

    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FilePath
    foreach ($arg in $Arguments) {
        [void]$psi.ArgumentList.Add($arg)
    }
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $p = [System.Diagnostics.Process]::new()
    $p.StartInfo = $psi
    [void]$p.Start()

    if (-not $p.WaitForExit($TimeoutSeconds * 1000)) {
        try { $p.Kill($true) } catch {}
        return [pscustomobject]@{
            ExitCode = 124
            Stdout = ""
            Stderr = "TIMEOUT after ${TimeoutSeconds}s: $FilePath $($Arguments -join ' ')"
            TimedOut = $true
        }
    }

    return [pscustomobject]@{
        ExitCode = $p.ExitCode
        Stdout = $p.StandardOutput.ReadToEnd()
        Stderr = $p.StandardError.ReadToEnd()
        TimedOut = $false
    }
}

function Start-WslKeepAlive {
    Write-Log "Starting WSL keepalive for distro=$Distro user=$User"
    Start-Process -WindowStyle Hidden -FilePath "wsl.exe" -ArgumentList @(
        "-d", $Distro,
        "-u", $User,
        "--",
        "bash",
        "-lc",
        "mkdir -p /tmp/codex_so101 && nohup bash -lc 'while true; do date -Is > /tmp/codex_so101/keepalive_heartbeat.txt; sleep 30; done' >/tmp/codex_so101/keepalive.log 2>&1 &"
    )
    Start-Sleep -Seconds 2
}

function Test-WslTty {
    $cmd = "test -e /dev/ttyACM0 && test -e /dev/serial/by-id/usb-1a86_USB_Single_Serial_${FollowerSerial}-if00 && readlink -f /dev/serial/by-id/usb-1a86_USB_Single_Serial_${FollowerSerial}-if00"
    $result = Invoke-ExeWithTimeout -FilePath "wsl.exe" -Arguments @("-d", $Distro, "-u", $User, "--", "bash", "-lc", $cmd) -TimeoutSeconds 8
    if ($result.TimedOut) {
        Write-Log "WSL follower check timed out; will refresh attach."
        return $false
    }
    if ($result.ExitCode -eq 0 -and ($result.Stdout -match "/dev/ttyACM0")) {
        Write-Log "WSL follower OK: $($result.Stdout.Trim())"
        return $true
    }
    Write-Log "WSL follower missing or not mapped to /dev/ttyACM0"
    return $false
}

function Attach-Follower {
    Write-Log "Refreshing follower USB attach: busid=$FollowerBusId"
    $detach = Invoke-ExeWithTimeout -FilePath "usbipd.exe" -Arguments @("detach", "--busid", $FollowerBusId) -TimeoutSeconds 6
    if ($detach.Stdout.Trim()) { Write-Host $detach.Stdout.Trim() }
    if ($detach.Stderr.Trim()) { Write-Host $detach.Stderr.Trim() }
    Start-Sleep -Seconds 1
    $attach = Invoke-ExeWithTimeout -FilePath "usbipd.exe" -Arguments @("attach", "--wsl", $Distro, "--busid", $FollowerBusId) -TimeoutSeconds 10
    if ($attach.Stdout.Trim()) { Write-Host $attach.Stdout.Trim() }
    if ($attach.Stderr.Trim()) { Write-Host $attach.Stderr.Trim() }
    Start-Sleep -Seconds 2
}

function Show-UsbState {
    Write-Log "usbipd state:"
    $state = Invoke-ExeWithTimeout -FilePath "usbipd.exe" -Arguments @("list") -TimeoutSeconds 6
    if ($state.Stdout.Trim()) { Write-Host $state.Stdout.Trim() }
    if ($state.Stderr.Trim()) { Write-Host $state.Stderr.Trim() }
}

Write-Log "SO101 WSL USB keepalive started. Distro=$Distro FollowerBusId=$FollowerBusId Serial=$FollowerSerial"
Start-WslKeepAlive

do {
    if (-not (Test-WslTty)) {
        Show-UsbState
        Attach-Follower
        [void](Test-WslTty)
    }

    if ($Once) {
        break
    }

    Start-Sleep -Seconds $CheckIntervalSeconds
} while ($true)

Write-Log "SO101 WSL USB keepalive finished."
