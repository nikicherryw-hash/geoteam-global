param(
  [Parameter(Mandatory=$true)][string]$PackageRoot,
  [Parameter(Mandatory=$true)][string]$SiteRoot
)

$source = Join-Path $PackageRoot 'public_ready_static'
if(!(Test-Path -LiteralPath $source)){ throw "Missing source package: $source" }
if(!(Test-Path -LiteralPath $SiteRoot)){ throw "Missing site root: $SiteRoot" }

$sourceFiles = Get-ChildItem -LiteralPath $source -Recurse -File
if(($sourceFiles | Where-Object Extension -eq '.html').Count -ne 133){ throw 'Expected exactly 133 HTML files in the package.' }

foreach($sourceFile in $sourceFiles){
  $relative = $sourceFile.FullName.Substring($source.Length).TrimStart('\')
  $target = Join-Path $SiteRoot $relative
  if(Test-Path -LiteralPath $target){ throw "Refusing to overwrite existing route: $relative" }
}

$targetHtml = @()
Get-ChildItem -LiteralPath $source -Force | ForEach-Object {
  Copy-Item -LiteralPath $_.FullName -Destination $SiteRoot -Recurse -Force
  if($_.PSIsContainer){
    $targetHtml += Get-ChildItem -LiteralPath (Join-Path $SiteRoot $_.Name) -Recurse -Filter '*.html'
  } elseif($_.Extension -eq '.html') {
    $targetHtml += Get-Item -LiteralPath (Join-Path $SiteRoot $_.Name)
  }
}

$headInjection = "`n<link rel=`"stylesheet`" href=`"/assets/geoteam-sector-shell.css`"/>`n<script defer src=`"/assets/geoteam-sector-shell.js`"></script>`n"
$targetHtml | ForEach-Object {
  $html = [IO.File]::ReadAllText($_.FullName)
  if($html -notmatch 'geoteam-sector-shell\.css'){
    $html = $html.Replace('</head>', "$headInjection</head>")
  }
  $html = [regex]::Replace($html, 'href="mailto:[^"]*"', 'href="/sourcing.html?lang=en"')
  $html = $html.Replace('href="/"', 'href="/index.html?lang=en"')
  [IO.File]::WriteAllText($_.FullName, $html, (New-Object Text.UTF8Encoding($false)))
}

$sitemap = @'
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://www.geoteam-global.com/sitemap-sectors.xml</loc></sitemap>
  <sitemap><loc>https://www.geoteam-global.com/sitemap-manufacturers.xml</loc></sitemap>
</sitemapindex>
'@
[IO.File]::WriteAllText((Join-Path $SiteRoot 'sitemap.xml'), $sitemap, (New-Object Text.UTF8Encoding($false)))
$robots = "User-agent: *`nDisallow: /`n"
[IO.File]::WriteAllText((Join-Path $SiteRoot 'robots.txt'), $robots, (New-Object Text.UTF8Encoding($false)))
Write-Output "Integrated $($sourceFiles.Count) package files; HTML=$((Get-ChildItem -LiteralPath $SiteRoot -Recurse -Filter '*.html').Count)"
