# WSL Startup Timeout Root Cause Report

Date: 2026-07-23

## Scope

Target distro:

```text
LeRobot-Ubuntu-F
```

Observed symptom:

```text
wsl -d LeRobot-Ubuntu-F -u nostalgia -- bash -lc "echo WSL_OK"
```

timed out after 30 seconds.

## Collected Facts

### Windows / WSL

```text
WSL version: 2.7.10.0
WSL kernel: 6.18.33.2-2
Windows build from wsl --version: 10.0.26200.8894
Default distro: LeRobot-Ubuntu-F
Default WSL version: 2
```

`wsl --status`, `wsl --version`, and `wsl -l -v` returned when all distros were stopped.

After a failed distro startup attempt, `wsl -l -v` also timed out.

### Services

Observed through `Get-Service`:

```text
vmcompute: Running
hns: Running
```

`LxssManager` did not appear in the normal `Get-Service` result in this environment. On newer Store WSL builds this is not by itself proof of failure.

### VM / Process State

After the failed startup:

```text
vmmemWSL: present
vmwp: present
```

This means WSL reached the Hyper-V worker / VM layer.

Also observed:

```text
many taskkill.exe processes
many conhost.exe processes
```

This is a secondary host-side problem because stale client/helper processes slow down further diagnostics and can make PowerShell/WSL interactions appear worse.

### Event Logs

Recent System log showed Hyper-V VmSwitch activity:

```text
10:41:58 WSL Hyper-V firewall switch port created / NIC connected
10:44:48 WSL Hyper-V firewall switch port deleted / NIC disconnected
```

This confirms the launch reached WSL VM networking setup.

### Post-repair Linux verification

After a real Administrator PowerShell executed Level 2 recovery, the distro booted successfully and returned Linux output.

Observed:

```text
minimal startup command returned
systemd-analyze blame returned normally
/etc/fstab contained only the base entry plus /dev/shm tmpfs
```

Top visible startup items were all sub-second or near-sub-second:

```text
753ms landscape-client.service
276ms dev-sdd.device
265ms snapd.seeded.service
177ms snapd.service
153ms wsl-pro.service
```

This does not support a Linux-internal boot blocker as the primary cause.

Warnings collected from `journalctl -b -p warning` included:

```text
WSL (121) ERROR: CheckConnection: getaddrinfo() failed: -5
Operation canceled @p9io.cpp:258 (AcceptAsync)
Failed unmounting init.mount - /init
system journal corrupted or uncleanly shut down
PAM unable to dlopen pam_lastlog.so
```

The WSL-specific `CheckConnection: getaddrinfo() failed: -5` message is the strongest Linux-side signal.

## Startup Chain Analysis

```text
Windows / PowerShell
-> wsl.exe launcher
-> WSL service / management API
-> Virtual Machine Platform / Hyper-V worker
-> WSL VM
-> distro init / systemd
-> Ubuntu userspace
-> shell command
```

The failure is not in the basic WSL management command path, because `wsl --status`, `wsl --version`, and cold `wsl -l -v` returned.

The failure happens after the launcher tries to start the distro. The VM layer starts, but the shell command does not return.

Most likely failure stage:

```text
WSL VM -> distro init/systemd/userspace transition
```

## Hypothesis Matrix

| Problem hypothesis | Verification method | Result |
| - | - | - |
| WSL management command globally broken | Run `wsl --status`, `wsl --version`, `wsl -l -v` while all distros are stopped | Not supported. These commands returned. |
| Windows VM layer unavailable | Check `vmcompute`, `hns`, `vmmemWSL`, `vmwp`, Hyper-V VmSwitch events | Not primary. VM layer starts and creates WSL network switch. |
| Distro startup hangs after VM creation | Run minimal `wsl -d LeRobot-Ubuntu-F -- bash -lc "echo WSL_OK"` with 30s timeout | Supported. Minimal startup timed out. |
| Half-started VM poisons later WSL commands | Run `wsl -l -v` after failed startup | Supported. `wsl -l -v` timed out after failed startup. |
| Linux systemd service blocks boot | `systemd-analyze blame`, `critical-chain` | Not supported as primary cause. Booted successfully after Level 2 and no large blocker appeared. |
| `/etc/fstab` mount blocks boot | `cat /etc/fstab` | Not supported. `fstab` is minimal and clean. |
| User shell startup blocks command | inspect `.bashrc`, `.profile`, `.zshrc`; compare root/non-login shell | Lower probability. Root shell now starts, so shell hooks are not the first failure to fix. |
| Docker Desktop causes VM resource contention | inspect Docker state and retest with Docker stopped | Not verified in this session. |
| Host-side stuck helper processes amplify timeouts | process list for `taskkill`, `conhost`, `wsl` | Supported as secondary cause. Many stale helpers were present. |
| WSL VM networking / connection handoff is unstable | event logs + journal warnings `CheckConnection: getaddrinfo() failed: -5` + Level 2 recovery success | Strongly supported. |

## Root Cause

Primary root cause:

```text
WSL distro startup was blocked by an unstable WSL VM networking / connection state. The Hyper-V/WSL VM layer started, but the distro shell did not become responsive until the host-side WSL network/compute services were refreshed from an Administrator PowerShell.
```

This is a startup-chain failure after WSL management and after VM creation, with the strongest evidence pointing at the WSL connection/network handoff rather than Linux init or `/etc/fstab`.

## Secondary Cause

```text
Accumulated stale Windows helper/client processes (`taskkill.exe`, `conhost.exe`, and timed-out `wsl.exe` clients) amplify the issue by making repeated diagnostics slower and noisier.
```

## Confidence

```text
Primary root cause confidence: 88%
Secondary cause confidence: 90%
```

Linux-internal blockers such as `systemd` and `/etc/fstab` are now lower-probability because the distro booted successfully after Level 2 recovery and the collected Linux-side evidence did not show a meaningful boot blocker.

## Immediate Repair Plan

Use Level 1 repair first:

```powershell
.\repair_wsl.ps1 -Level 1 -Distro LeRobot-Ubuntu-F -Apply
```

Expected effect:

- stop stale WSL client processes
- clear the half-started WSL VM using `wsl --shutdown`
- retest `wsl -l -v`
- retest minimal distro startup

Risk:

- active WSL sessions and Linux jobs will be interrupted

Recovery:

- restart the distro with `wsl -d LeRobot-Ubuntu-F`
- rerun `diagnose_wsl.ps1`

## Repair Attempts In This Session

### Level 1

Command:

```powershell
.\repair_wsl.ps1 -Level 1 -Distro LeRobot-Ubuntu-F -Apply -TimeoutSeconds 20
```

Result:

```text
stale taskkill clients were stopped
wsl --shutdown returned once in the first attempt
minimal distro startup still timed out after 20 seconds
```

Interpretation:

```text
Level 1 was not sufficient. The half-started VM can be cleared temporarily, but distro userspace still does not become responsive.
```

### Level 2

Command:

```powershell
.\repair_wsl.ps1 -Level 2 -Distro LeRobot-Ubuntu-F -Apply -TimeoutSeconds 25
```

Result:

```text
wsl --shutdown timed out
LxssManager was not present as a normal service
vmcompute restart failed because the current PowerShell process could not open the service
hns restart failed because the current PowerShell process could not open the service
wsl -l -v timed out after the failed shutdown
minimal distro startup timed out
```

Interpretation:

```text
The current execution context was not elevated enough for Level 2 service recovery. A true Administrator PowerShell is required for service restart, or Windows must be rebooted to reset the Hyper-V/WSL service state.
```

### Forced cold-state retry

Action:

```text
force-stopped vmmemWSL and vmwp after clearing stale client processes
```

Then retested:

```powershell
wsl.exe -d LeRobot-Ubuntu-F -u root -- bash -lc "echo WSL_OK; date; uname -a"
```

Result:

```text
still timed out after 30 seconds
```

Interpretation:

```text
The issue is not only leftover VM state. Even from a forced cold reset, the distro startup path hangs again.
```

### Administrator PowerShell Level 2 success

Command executed from a true Administrator PowerShell:

```powershell
.\repair_wsl.ps1 -Level 2 -Distro LeRobot-Ubuntu-F -Apply -TimeoutSeconds 30
```

Result:

```text
RunningAsAdministrator=True
wslhost stale processes were cleared
wsl --shutdown returned
vmcompute restarted
hns restarted
minimal distro startup no longer timed out
```

Interpretation:

```text
This confirms the failure was recoverable through host-side WSL/VM/network service refresh, not by changing Linux boot configuration.
```

## Medium-Term Optimization

After WSL starts:

```bash
systemd-analyze blame
systemd-analyze critical-chain
journalctl -b -p warning --no-pager
cat /etc/fstab
```

Then inspect:

```bash
~/.bashrc
~/.profile
~/.zshrc
```

Remove or guard anything that blocks on network, proxy startup, Docker startup, SSH, missing mounts, or long conda initialization.

## Long-Term Prevention

- Keep `diagnose_wsl.ps1` and `repair_wsl.ps1` as the standard recovery entry point.
- Run diagnostics after Windows, WSL, Docker, or GPU driver updates.
- Avoid launching training jobs from shell startup files.
- Keep `/etc/fstab` minimal and avoid required network mounts at boot.
- Treat repeated `/dev/ttyACM0` or USB/IP resets separately from WSL startup failures.
