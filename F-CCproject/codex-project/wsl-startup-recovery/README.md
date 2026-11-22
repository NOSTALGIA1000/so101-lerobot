# WSL Startup Recovery

This folder contains a repeatable WSL startup diagnosis and recovery SOP.

## Files

```text
WSL_STARTUP_RECOVERY_SKILL.md
diagnose_wsl.ps1
repair_wsl.ps1
ROOT_CAUSE_REPORT_20260723.md
```

## Diagnose First

Run from PowerShell:

```powershell
cd C:\Users\ASUS\Documents\lerobot\F-CCproject\codex-project\wsl-startup-recovery
.\diagnose_wsl.ps1 -Distro LeRobot-Ubuntu-F
```

If WSL startup is known to hang and you only want Windows-side evidence:

```powershell
.\diagnose_wsl.ps1 -Distro LeRobot-Ubuntu-F -SkipLinuxStartup
```

Output:

```text
wsl_diagnosis_report.txt
```

## Repair

Preview actions:

```powershell
.\repair_wsl.ps1 -Level 1 -Distro LeRobot-Ubuntu-F
```

Apply Level 1 recovery:

```powershell
.\repair_wsl.ps1 -Level 1 -Distro LeRobot-Ubuntu-F -Apply
```

Apply Level 2 only if Level 1 fails:

```powershell
.\repair_wsl.ps1 -Level 2 -Distro LeRobot-Ubuntu-F -Apply
```

## Recovery Levels

```text
Level 1: stop stale WSL client processes and clear the half-started WSL VM
Level 2: restart WSL-adjacent Windows services
Level 3: inspect Linux startup once WSL can boot
Level 4: manual export/import only after backup
```

## Safety

- `diagnose_wsl.ps1` is read-only except for writing its report file.
- `repair_wsl.ps1` does nothing unless `-Apply` is provided.
- Level 1 can interrupt active WSL sessions.
- Level 2 can interrupt Docker Desktop and WSL networking.
- Level 4 is intentionally not automated.

## Recommended Workflow

1. Run `diagnose_wsl.ps1`.
2. Read `wsl_diagnosis_report.txt`.
3. If distro startup hangs and `vmmemWSL` remains, run Level 1 repair.
4. If management commands still hang, run Level 2 repair.
5. After WSL boots, run Linux startup checks for `systemd`, `/etc/fstab`, and shell startup files.
