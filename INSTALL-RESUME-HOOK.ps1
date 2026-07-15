#requires -Version 5.1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$root = "D:\"
$baseUrl = "https://raw.githubusercontent.com/Topbrutus/Antmux/main"
$hooksDirectory = Join-Path $root "hooks"
$summaryDirectory = Join-Path $root "communication\resumes"
$hooksConfig = Join-Path $root "hooks.json"
$hookScript = Join-Path $hooksDirectory "save-summary.ps1"

$drive = [System.IO.DriveInfo]::new($root)
if (-not $drive.IsReady) {
    throw "Le disque D: n'est pas pret."
}
if ($drive.VolumeLabel -ine "Antmux") {
    throw "Le disque D: doit porter le nom Antmux. Nom actuel : '$($drive.VolumeLabel)'."
}

New-Item -ItemType Directory -Force -Path $hooksDirectory | Out-Null
New-Item -ItemType Directory -Force -Path $summaryDirectory | Out-Null

if (Test-Path -LiteralPath $hooksConfig -PathType Leaf) {
    $backup = Join-Path $root ("hooks.backup.{0}.json" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
    Copy-Item -LiteralPath $hooksConfig -Destination $backup -Force
    Write-Host "Ancien hooks.json sauvegarde : $backup"
}

Invoke-WebRequest -UseBasicParsing `
    -Uri "$baseUrl/hooks.json" `
    -OutFile $hooksConfig

Invoke-WebRequest -UseBasicParsing `
    -Uri "$baseUrl/hooks/save-summary.ps1" `
    -OutFile $hookScript

$null = Get-Content -LiteralPath $hooksConfig -Raw | ConvertFrom-Json
$parseTokens = $null
$parseErrors = $null
$null = [System.Management.Automation.Language.Parser]::ParseFile(
    $hookScript,
    [ref]$parseTokens,
    [ref]$parseErrors
)
if ($parseErrors.Count -gt 0) {
    throw "Le script du hook contient une erreur PowerShell : $($parseErrors[0].Message)"
}

Write-Host ""
Write-Host "HOOK DE RESUME INSTALLE" -ForegroundColor Green
Write-Host "Configuration : $hooksConfig"
Write-Host "Script        : $hookScript"
Write-Host "Destination   : $summaryDirectory"
Write-Host ""
Write-Host "Redemarre Antmux, tape /hooks, puis approuve le hook Stop."
Write-Host "Un resume sera copie seulement s'il contient les marqueurs :"
Write-Host "DEBUT DU RESUME ... FIN DU TERMINAL"
