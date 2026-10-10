# ============================================================
#  QQNT 防撤回一键补丁脚本
#  适用：QQ 9.9.36-53644 / wrapper.node 9.8.0.24541
#  原理：定位 4 处撤回消息长度检查分支 (0F 87 -> 0F 86)
#  用法：右键本文件 -> 使用 PowerShell 运行（或管理员 PowerShell 执行）
#  备份：自动备份原文件为 wrapper.node.bak
#  风险：官方说明防撤回存在封号/警告风险，使用后果自负
# ============================================================
param(
  [string]$Path = "D:\Program Files\Tencent\QQNT\versions\9.9.36-53644\resources\app\wrapper.node"
)
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Path)) {
  Write-Host "[-] 找不到文件: $Path"
  Write-Host "    请检查 QQ 版本是否为 9.9.36-53644，或用 -Path 指定 wrapper.node 路径"
  try { Read-Host "按回车退出" } catch {}
  exit 1
}

$bytes = [System.IO.File]::ReadAllBytes($Path)

# 特征：4C 89 C0 48 29 D0 48 83 F8 07 0F 87
$pattern = [byte[]](0x4C, 0x89, 0xC0, 0x48, 0x29, 0xD0, 0x48, 0x83, 0xF8, 0x07, 0x0F, 0x87)

$hits = New-Object System.Collections.Generic.List[int]
for ($i = 0; $i -le $bytes.Length - $pattern.Length; $i++) {
  $ok = $true
  for ($j = 0; $j -lt $pattern.Length; $j++) {
    if ($bytes[$i + $j] -ne $pattern[$j]) { $ok = $false; break }
  }
  if ($ok) { $hits.Add($i) }
}

Write-Host ("[*] 特征匹配 " + $hits.Count + " 处")
if ($hits.Count -eq 0) {
  Write-Host "[-] 0 匹配：可能已打过补丁，或当前 wrapper.node 版本不适用"
  try { Read-Host "按回车退出" } catch {}
  exit 0
}
if ($hits.Count -ne 4) {
  Write-Host "[-] 匹配数不是 4，为安全起见中止（文件可能已被其他补丁修改）"
  try { Read-Host "按回车退出" } catch {}
  exit 1
}

# 备份（只在第一次运行时备份）
$bak = $Path + ".bak"
if (-not (Test-Path -LiteralPath $bak)) {
  [System.IO.File]::Copy($Path, $bak)
  Write-Host ("[+] 已备份原文件 -> " + $bak)
}

# 修改 0F 87 -> 0F 86
foreach ($h in $hits) { $bytes[$h + 11] = 0x86 }

[System.IO.File]::WriteAllBytes($Path, $bytes)
Write-Host "[+] 补丁完成！已修改 4 处 (0F 87 -> 0F 86)"
Write-Host "[*] 重启 QQ 生效。QQ 自动更新会覆盖补丁，失效后重新运行本脚本即可。"
try { Read-Host "按回车退出" } catch {}
