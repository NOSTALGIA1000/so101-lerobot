param(
    [string]$Distro = "LeRobot-Ubuntu-F",
    [string]$OutputPath = ".\wsl_diagnosis_report.txt",
    [int]$TimeoutSeconds = 15,
    [int]$EventHours = 6,
    [int]$MaxEvents = 80,
    [switch]$SkipLinuxStartup
)

$ErrorActionPreference = "Continue"

function Add-Section {
    param([string]$Title)
    Add-Content -LiteralPath $script:ReportPath -Value ""
    Add-Content -LiteralPath $script:ReportPath -Value ("=" * 80)
    Add-Content -LiteralPath $script:ReportPath -Value $Title
    Add-Content -LiteralPath $script:ReportPath -Value ("=" * 80)
}

function Add-Line {
    param([string]$Text)
    Add-Content -LiteralPath $script:ReportPath -Value $Text
}

function Invoke-Captured {
    param(
        [string]$Label,
        [string]$FilePath,
        [string[]]$Arguments,
        [int]$Timeout = $script:TimeoutSeconds
    )

    Add-Section $Label
    Add-Line ("COMMAND: {0} {1}" -f $FilePath, ($Arguments -join " "))

    $outFile = Join-Path $env:TEMP ("wsl_diag_out_{0}.txt" -f ([guid]::NewGuid()))
    $errFile = Join-Path $env:TEMP ("wsl_diag_err_{0}.txt" -f ([guid]::NewGuid()))
    $sw = [Diagnostics.Stopwatch]::StartNew()

    try {
        $p = Start-Process -FilePath $FilePath -ArgumentList $Arguments -NoNewWindow -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
        if (-not $p.WaitForExit($Timeout * 1000)) {
            $sw.Stop()
            Add-Line ("RESULT: TIMEOUT_AFTER_{0}s elapsed_ms={1}" -f $Timeout, $sw.ElapsedMilliseconds)
            try { $p.Kill() } catch { Add-Line ("KILL_FAILED: {0}" -f $_.Exception.Message) }
        } else {
            $sw.Stop()
            Add-Line ("RESULT: EXIT exit_code={0} elapsed_ms={1}" -f $p.ExitCode, $sw.ElapsedMilliseconds)
        }

        if (Test-Path -LiteralPath $outFile) {
            Add-Line "--- stdout ---"
            Get-Content -LiteralPath $outFile -ErrorAction SilentlyContinue | Add-Content -LiteralPath $script:ReportPath
        }
        if (Test-Path -LiteralPath $errFile) {
            Add-Line "--- stderr ---"
            Get-Content -LiteralPath $errFile -ErrorAction SilentlyContinue | Add-Content -LiteralPath $script:ReportPath
        }
    } catch {
        Add-Line ("ERROR: {0}" -f $_.Exception.Message)
    } finally {
        Remove-Item -LiteralPath $outFile,$errFile -Force -ErrorAction SilentlyContinue
    }
}

function Add-ObjectOutput {
    param(
        [string]$Title,
        [scriptblock]$Script
    )

    Add-Section $Title
    try {
        (& $Script | Out-String -Width 240).TrimEnd() | Add-Content -LiteralPath $script:ReportPath
    } catch {
        Add-Line ("ERROR: {0}" -f $_.Exception.Message)
    }
}

$script:TimeoutSeconds = $TimeoutSeconds
$script:ReportPath = (Resolve-Path -LiteralPath (Split-Path -Parent $OutputPath) -ErrorAction SilentlyContinue)
if (-not $script:ReportPath) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $OutputPath) -Force -ErrorAction SilentlyContinue | Out-Null
}
$script:ReportPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)

Set-Content -LiteralPath $script:ReportPath -Value "WSL Diagnosis Report"
Add-Line ("Generated: {0}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"))
Add-Line ("Distro: {0}" -f $Distro)
Add-Line ("TimeoutSeconds: {0}" -f $TimeoutSeconds)
Add-Line ("SkipLinuxStartup: {0}" -f [bool]$SkipLinuxStartup)

Add-ObjectOutput "Windows Version" {
    [pscustomobject]@{
        ProductName = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" -ErrorAction SilentlyContinue).ProductName
        DisplayVersion = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" -ErrorAction SilentlyContinue).DisplayVersion
        CurrentBuild = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" -ErrorAction SilentlyContinue).CurrentBuild
        UBR = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" -ErrorAction SilentlyContinue).UBR
        OSArchitecture = (Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue).OSArchitecture
    }
}

Add-ObjectOutput "WSL Optional Features" {
    foreach ($feature in "Microsoft-Windows-Subsystem-Linux","VirtualMachinePlatform","Microsoft-Hyper-V-All") {
        try {
            Get-WindowsOptionalFeature -Online -FeatureName $feature | Select-Object FeatureName,State
        } catch {
            [pscustomobject]@{ FeatureName = $feature; State = "UNKNOWN_OR_NEEDS_ELEVATION"; Error = $_.Exception.Message }
        }
    }
}

Invoke-Captured "wsl --status" "wsl.exe" @("--status")
Invoke-Captured "wsl --version" "wsl.exe" @("--version")
Invoke-Captured "wsl -l -v" "wsl.exe" @("-l","-v")

Add-ObjectOutput "Services" {
    Get-Service LxssManager,vmcompute,hns,vmms -ErrorAction SilentlyContinue | Select-Object Name,Status,StartType,ServiceType
}

Add-ObjectOutput "WSL Related Processes" {
    Get-Process wsl,wslhost,vmmemWSL,vmmem,vmwp,taskkill,conhost -ErrorAction SilentlyContinue |
        Select-Object ProcessName,Id,CPU,WorkingSet64,StartTime |
        Sort-Object ProcessName,Id
}

Add-ObjectOutput "Resource Snapshot" {
    $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
    $disks = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" -ErrorAction SilentlyContinue
    [pscustomobject]@{
        TotalMemoryMB = if ($os) { [math]::Round($os.TotalVisibleMemorySize / 1024, 1) } else { $null }
        FreeMemoryMB = if ($os) { [math]::Round($os.FreePhysicalMemory / 1024, 1) } else { $null }
    }
    $disks | Select-Object DeviceID,@{Name="SizeGB";Expression={[math]::Round($_.Size/1GB,1)}},@{Name="FreeGB";Expression={[math]::Round($_.FreeSpace/1GB,1)}}
}

Add-ObjectOutput "Event Log Channels" {
    wevtutil el | Select-String -Pattern "Linux|Lxss|Hyper-V|HNS|Host-Network|VmCompute|Subsystem"
}

Add-ObjectOutput "Recent System Events" {
    Get-WinEvent -FilterHashtable @{LogName="System"; StartTime=(Get-Date).AddHours(-1 * $EventHours)} -MaxEvents 500 -ErrorAction SilentlyContinue |
        Where-Object {
            $_.ProviderName -match "Lxss|Hyper-V|Host-Network|Service Control|Virtual|hns|vmcompute" -or
            $_.Message -match "wsl|timeout|failed|hang|vm|mount|network|filesystem|Lxss|HNS|Hyper-V"
        } |
        Select-Object TimeCreated,ProviderName,Id,LevelDisplayName,Message -First $MaxEvents
}

if (-not $SkipLinuxStartup) {
    Invoke-Captured "Minimal Linux Startup Probe" "wsl.exe" @("-d",$Distro,"-u","root","--","bash","-lc","echo WSL_OK; date; uname -a") -Timeout $TimeoutSeconds
    Invoke-Captured "Linux systemd-analyze" "wsl.exe" @("-d",$Distro,"-u","root","--","bash","-lc","systemd-analyze blame --no-pager | head -80; systemd-analyze critical-chain --no-pager") -Timeout $TimeoutSeconds
    Invoke-Captured "Linux warnings and fstab" "wsl.exe" @("-d",$Distro,"-u","root","--","bash","-lc","journalctl -b -p warning --no-pager | tail -120; printf '\n--- /etc/fstab ---\n'; cat /etc/fstab") -Timeout $TimeoutSeconds
    Invoke-Captured "Linux shell startup files" "wsl.exe" @("-d",$Distro,"-u","root","--","bash","-lc",'for f in /home/*/.bashrc /home/*/.profile /home/*/.zshrc; do if [ -f "$f" ]; then echo "--- $f ---"; sed -n "1,220p" "$f"; fi; done') -Timeout $TimeoutSeconds
}

Add-Section "End"
Add-Line "Report complete."
Write-Output ("Report written: {0}" -f $script:ReportPath)
