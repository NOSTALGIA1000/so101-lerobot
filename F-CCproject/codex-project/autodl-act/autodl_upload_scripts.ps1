param(
  [string]$HostName = "connect.bjb1.seetacloud.com",
  [int]$Port = 45311
)

$ErrorActionPreference = "Stop"
$localDir = "C:\tmp\so101_autodl"
$sourceDir = "C:\Users\ASUS\Documents\lerobot\F-CCproject\codex-project\autodl-act"
$remote = "root@${HostName}:/root/so101_autodl/"

New-Item -ItemType Directory -Force -Path $localDir | Out-Null
Copy-Item -Force "$sourceDir\autodl_so101_setup_env.sh" $localDir
Copy-Item -Force "$sourceDir\autodl_train_v2.sh" $localDir
Copy-Item -Force "$sourceDir\autodl_merge_v3v6.sh" $localDir
Copy-Item -Force "$sourceDir\autodl_train_v3v6.sh" $localDir
Copy-Item -Force "$sourceDir\autodl_train_v4.sh" $localDir
Copy-Item -Force "$sourceDir\autodl_train_v5.sh" $localDir
Copy-Item -Force "$sourceDir\autodl_train_uploaded_v2.sh" $localDir
Copy-Item -Force "$sourceDir\autodl_train_uploaded_v7.sh" $localDir
Copy-Item -Force "$sourceDir\autodl_monitor.sh" $localDir
Copy-Item -Force "$sourceDir\autodl_package_ckpt.sh" $localDir

ssh -p $Port "root@$HostName" "mkdir -p /root/so101_autodl /root/autodl-tmp"
scp -P $Port "$localDir\*.sh" $remote
ssh -p $Port "root@$HostName" "chmod +x /root/so101_autodl/*.sh"

Write-Host "Uploaded scripts to /root/so101_autodl"
