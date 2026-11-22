param(
  [string]$HostName = "connect.bjb1.seetacloud.com",
  [int]$Port = 45311,
  [ValidateSet("v2", "v3v6")]
  [string]$RunName = "v2"
)

$ErrorActionPreference = "Stop"
$localDir = "C:\Users\ASUS\Documents\lerobot\checkpoints\autodl"
New-Item -ItemType Directory -Force -Path $localDir | Out-Null

$remoteListCmd = "ls -1 /root/autodl-tmp/so101_ckpt_packages/${RunName}_*_pretrained_model.tar.gz | tail -1"
$pkg = ssh -p $Port "root@$HostName" $remoteListCmd
if (-not $pkg) {
  throw "No package found for $RunName. Run: bash /root/so101_autodl/autodl_package_ckpt.sh $RunName"
}

scp -P $Port "root@${HostName}:$pkg" "$localDir\"
Write-Host "Downloaded $pkg to $localDir"

