[CmdletBinding()]
param(
  [string]$SiteRoot = (Join-Path $PSScriptRoot '..\preview-v18-7'),
  [switch]$RequireComplete
)

$ErrorActionPreference = 'Stop'
$site = (Resolve-Path -LiteralPath $SiteRoot).Path
$languages = @('en','tr','ru','de','fr','es','it','pt','ar','zh')
$sectorDirectories = @('aviation','industrial','electronics','marine')
$rootPages = @('aviation.html','industrial.html','electronics.html','marine.html','manufacturers.html')

$routes = [System.Collections.Generic.List[string]]::new()
foreach ($page in $rootPages) { $routes.Add($page) }
foreach ($sector in $sectorDirectories) {
  Get-ChildItem -LiteralPath (Join-Path $site $sector) -Filter '*.html' -File -Recurse |
    ForEach-Object { $routes.Add($_.FullName.Substring($site.Length + 1).Replace('\','/')) }
}
$routes = @($routes | Sort-Object -Unique)
if ($routes.Count -ne 133) { throw "Expected 133 sector routes, found $($routes.Count)." }

$missing = [System.Collections.Generic.List[string]]::new()
$wrongLanguage = [System.Collections.Generic.List[string]]::new()
foreach ($language in $languages) {
  foreach ($route in $routes) {
    $path = if ($language -eq 'en') { Join-Path $site $route } else { Join-Path (Join-Path $site $language) $route }
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
      $missing.Add("$language/$route")
      continue
    }
    $content = Get-Content -LiteralPath $path -Raw
    if ($content -notmatch ('<html\s+lang=["'']' + [regex]::Escape($language) + '["'']')) {
      $wrongLanguage.Add("$language/$route")
    }
  }
}

$result = [ordered]@{
  base_routes = $routes.Count
  expected_localized_pages = $routes.Count * $languages.Count
  languages = $languages
  present_pages = ($routes.Count * $languages.Count) - $missing.Count
  missing_pages = $missing.Count
  wrong_html_lang = $wrongLanguage.Count
  complete = ($missing.Count -eq 0 -and $wrongLanguage.Count -eq 0)
  missing_sample = @($missing | Select-Object -First 20)
  wrong_language_sample = @($wrongLanguage | Select-Object -First 20)
}

$result | ConvertTo-Json -Depth 4
if ($RequireComplete -and -not $result.complete) { exit 1 }
