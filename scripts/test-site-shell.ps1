[CmdletBinding()]
param([string]$Root = (Join-Path $PSScriptRoot '..\preview-v18-7'))

$ErrorActionPreference = 'Stop'
$site = (Resolve-Path $Root).Path
$all = Get-ChildItem -LiteralPath $site -Recurse -File -Filter '*.html'
$internal = $all | Where-Object { -not ($_.Name -eq 'index.html' -and $_.DirectoryName -eq $site) }
$missingShell = @($internal | Where-Object { -not (Select-String -LiteralPath $_.FullName -Quiet -Pattern 'geoteam-site-shell\.css') })
$legacyShell = @($all | Where-Object { Select-String -LiteralPath $_.FullName -Quiet -Pattern 'geoteam-sector-shell' })
$missingHead = @($internal | Where-Object { -not (Select-String -LiteralPath $_.FullName -Quiet -Pattern '</head>') })
$assets = @('assets/geoteam-site-shell.css','assets/geoteam-site-shell.js') | ForEach-Object { Join-Path $site $_ }
$result = [ordered]@{
  html_total = $all.Count
  internal_html_total = $internal.Count
  shell_coverage = $internal.Count - $missingShell.Count
  shell_missing = $missingShell.Count
  legacy_shell_references = $legacyShell.Count
  missing_head = $missingHead.Count
  shell_assets_present = @($assets | ForEach-Object { Test-Path -LiteralPath $_ }) -notcontains $false
  status = if ($missingShell.Count -eq 0 -and $legacyShell.Count -eq 0 -and $missingHead.Count -eq 0) { 'PASS' } else { 'FAIL' }
}
$result | ConvertTo-Json
if ($result.status -ne 'PASS') { exit 1 }
