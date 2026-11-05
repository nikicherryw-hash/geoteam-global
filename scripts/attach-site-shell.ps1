param(
  [string]$Root = (Join-Path $PSScriptRoot '..\preview-v18-7')
)

$rootPath = (Resolve-Path $Root).Path
$assetTags = @'
<link rel="stylesheet" href="/assets/geoteam-site-shell.css?v=20261106-unified" />
<script defer src="/assets/geoteam-site-shell.js?v=20261106-unified"></script>
'@

$updated = 0
Get-ChildItem -LiteralPath $rootPath -Recurse -File -Filter '*.html' | ForEach-Object {
  if ($_.Name -eq 'index.html' -and $_.DirectoryName -eq $rootPath) { return }
  $html = [System.IO.File]::ReadAllText($_.FullName)
  $next = [regex]::Replace($html, '\s*<link[^>]+geoteam-sector-shell\.css[^>]*>\s*', "`n")
  $next = [regex]::Replace($next, '\s*<script[^>]+geoteam-sector-shell\.js[^>]*></script>\s*', "`n")
  if ($next -notmatch 'geoteam-site-shell\.css') {
    $next = $next -replace '</head>', "$assetTags</head>"
  }
  if ($next -ne $html) {
    [System.IO.File]::WriteAllText($_.FullName, $next, [System.Text.UTF8Encoding]::new($false))
    $updated++
  }
}
Write-Output "UPDATED_HTML=$updated"
