# WSL Startup Recovery Skill

## 1. Purpose

Use this skill when WSL startup hangs, `wsl.exe` times out, distro commands never reach the shell, or WSL leaves `vmmemWSL` / `vmwp` running after a failed start.

The goal is to separate four failure classes:

- Windows virtualization layer failure
- WSL service / launcher failure
- Linux init or systemd failure
- User shell / developer environment failure

Do not start with destructive repair. Always collect a diagnostic report first.

## 2. Environment Check

Collect these Windows facts first:

```powershell
.\diagnose_wsl.ps1 -Distro LeRobot-Ubuntu-F
```

The report must include:

- Windows version and build
- WSL version and kernel
- `wsl --status`
- `wsl --version`
- `wsl -l -v`
- `LxssManager`, `vmcompute`, `hns`, and `vmms` service state
- `wsl`, `wslhost`, `vmmemWSL`, `vmwp`, `taskkill`, and `conhost` process state
- CPU, memory, and disk state
- recent Hyper-V, HNS, vmcompute, and WSL-related event logs

## 3. Startup Diagnosis Pipeline

### Step 1: Check WSL management state

Run `wsl --status`, `wsl --version`, and `wsl -l -v` with a timeout.

Interpretation:

- If these commands hang while no distro is running, suspect WSL service or Windows virtualization state.
- If these commands work before distro startup but hang after a distro startup attempt, suspect a half-started WSL VM.

### Step 2: Check Windows services

Inspect:

```powershell
Get-Service LxssManager,vmcompute,hns,vmms -ErrorAction SilentlyContinue
```

Interpretation:

- `vmcompute` and `hns` must be available for WSL2 networking and VM lifecycle.
- `LxssManager` may not appear as a normal service on newer Store WSL builds; record absence instead of assuming failure.

### Step 3: Check VM layer

Inspect:

```powershell
Get-Process vmmemWSL,vmwp,wsl,wslhost -ErrorAction SilentlyContinue
```

Interpretation:

- `vmmemWSL` / `vmwp` present after a failed command means WSL VM reached the Hyper-V worker stage.
- If `wsl -l -v` then times out, the VM is likely half-started.

### Step 4: Check Linux startup

Only after WSL can execute Linux commands:

```bash
systemd-analyze blame
systemd-analyze critical-chain
journalctl -b -p warning --no-pager
cat /etc/fstab
```

Look for:

- blocked mount units
- missing disks
- network mounts
- slow systemd services
- scripts that wait on network or external devices
- WSL-specific warnings such as `CheckConnection: getaddrinfo() failed: -5`

### Step 5: Check user environment

Only after root shell works:

```bash
sed -n '1,220p' ~/.bashrc
sed -n '1,220p' ~/.profile
sed -n '1,220p' ~/.zshrc 2>/dev/null
```

Look for:

- automatic proxy startup
- SSH commands
- conda activation that runs heavy scripts
- Docker startup
- network probes
- long-running shell hooks

## 4. Automatic Diagnostic Commands

Use:

```powershell
.\diagnose_wsl.ps1 -Distro LeRobot-Ubuntu-F
```

Output:

```text
wsl_diagnosis_report.txt
```

Use `-SkipLinuxStartup` when even a minimal WSL launch is known to hang and you only want Windows-side evidence.

## 5. Recovery Procedure

Use `repair_wsl.ps1` with `-Apply`. Without `-Apply`, it prints the planned actions.

### Level 1: Simple recovery

Purpose: clear stuck client processes and shut down the half-started WSL VM.

```powershell
.\repair_wsl.ps1 -Level 1 -Apply
```

Risk:

- stops active WSL sessions
- interrupts running Linux jobs

Recovery:

- restart the distro with `wsl -d <distro>`

### Level 2: Service refresh

Purpose: restart WSL-adjacent services after Level 1 fails.

```powershell
.\repair_wsl.ps1 -Level 2 -Apply
```

Risk:

- may interrupt Docker Desktop, WSL networking, and containers

Recovery:

- reopen Docker Desktop if used
- rerun `wsl -l -v`

Use Level 2 early when these symptoms appear together:

```text
wsl --status works
minimal distro startup hangs
vmmemWSL / vmwp appear
journal or host logs mention WSL CheckConnection / getaddrinfo failures
```

### Level 3: Linux repair

Purpose: inspect Linux startup blockers after WSL can boot.

Manual checks:

```bash
systemd-analyze blame
systemd-analyze critical-chain
journalctl -b -p warning --no-pager
cat /etc/fstab
```

Risk:

- editing `/etc/fstab` or shell startup files can prevent expected mounts or environment setup

Backup:

```bash
sudo cp /etc/fstab /etc/fstab.bak.$(date +%Y%m%d_%H%M%S)
cp ~/.bashrc ~/.bashrc.bak.$(date +%Y%m%d_%H%M%S)
cp ~/.profile ~/.profile.bak.$(date +%Y%m%d_%H%M%S)
```

Recovery:

```bash
sudo cp /etc/fstab.bak.<timestamp> /etc/fstab
cp ~/.bashrc.bak.<timestamp> ~/.bashrc
cp ~/.profile.bak.<timestamp> ~/.profile
```

### Level 4: Re-register distro

Purpose: last resort for a damaged distro registration.

Do not run automatically. Export first:

```powershell
wsl --export <distro> <backup.tar>
```

Risk:

- incorrect unregister/import can lose the distro

Recovery:

```powershell
wsl --import <new-name> <install-dir> <backup.tar> --version 2
```

## 6. Prevention Checklist

Monthly:

- `wsl --update`
- verify free disk space on the distro drive
- check Docker Desktop resource limits
- inspect `/etc/fstab` for obsolete mounts
- keep shell startup files free of blocking network calls
- avoid launching long training jobs directly from `.bashrc` or `.profile`
- run `diagnose_wsl.ps1` and archive the report after major Windows or WSL updates
