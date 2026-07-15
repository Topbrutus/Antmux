#requires -Version 5.1
<#+
.SYNOPSIS
Répare l'installation Antmux lorsque Node.js est présent sur D:\ mais que @openai/codex et antmux.cmd sont absents.
#>

[CmdletBinding()]
param(
    [string]$Root = "D:\"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Write-Step {
    param([Parameter(Mandatory = $true)][string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Normalize-Root {
    param([Parameter(Mandatory = $true)][string]$Path)

    $full = [System.IO.Path]::GetFullPath($Path)
    $driveRoot = [System.IO.Path]::GetPathRoot($full)
    if ($full.TrimEnd([char]92) -ne $driveRoot.TrimEnd([char]92)) {
        throw "La cible doit être exactement la racine d'un disque : $Path"
    }
    return $driveRoot
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Add-PathEntry {
    param([Parameter(Mandatory = $true)][string]$Entry)

    $normalized = $Entry.TrimEnd([char]92)

    $sessionEntries = @($env:Path.Split(';', [System.StringSplitOptions]::RemoveEmptyEntries))
    if (-not ($sessionEntries | Where-Object { $_.TrimEnd([char]92) -ieq $normalized })) {
        $env:Path = "$Entry;$env:Path"
    }

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $userEntries = @()
    if (-not [string]::IsNullOrWhiteSpace($userPath)) {
        $userEntries = @($userPath.Split(';', [System.StringSplitOptions]::RemoveEmptyEntries))
    }

    if (-not ($userEntries | Where-Object { $_.TrimEnd([char]92) -ieq $normalized })) {
        $newUserPath = if ([string]::IsNullOrWhiteSpace($userPath)) {
            $Entry
        } else {
            "$Entry;$userPath"
        }
        [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
    }
}

$Root = Normalize-Root -Path $Root
$NodeExe = Join-Path $Root "node.exe"
$NpmCli = Join-Path $Root "node_modules\npm\bin\npm-cli.js"
$PackageDir = Join-Path $Root "node_modules\@openai\codex"
$ManifestPath = Join-Path $PackageDir "package.json"
$AntmuxCmd = Join-Path $Root "antmux.cmd"
$NpmConfig = Join-Path $Root ".npmrc"
$NpmCache = Join-Path $Root ".npm-cache"
$TempDir = Join-Path $Root ".antmux-temp"
$AppDataDir = Join-Path $Root ".antmux-appdata"
$LocalAppDataDir = Join-Path $Root ".antmux-localappdata"
$NpmLog = Join-Path $Root "antmux-npm-install.log"

Write-Step "Validation de Node.js et npm sur $Root"
if (-not (Test-Path -LiteralPath $NodeExe -PathType Leaf)) {
    throw "Node.js est absent : $NodeExe"
}
if (-not (Test-Path -LiteralPath $NpmCli -PathType Leaf)) {
    throw "Le moteur npm est absent : $NpmCli"
}

foreach ($directory in @($NpmCache, $TempDir, $AppDataDir, $LocalAppDataDir)) {
    Ensure-Directory -Path $directory
}

# Isolation de l'environnement Antmux sur D:\.
$env:ANTMUX_ROOT = $Root
$env:CODEX_HOME = $Root
$env:HOME = $Root
$env:XDG_CONFIG_HOME = $Root
$env:XDG_CACHE_HOME = $LocalAppDataDir
$env:APPDATA = $AppDataDir
$env:LOCALAPPDATA = $LocalAppDataDir
$env:TEMP = $TempDir
$env:TMP = $TempDir
$env:NPM_CONFIG_PREFIX = $Root
$env:NPM_CONFIG_CACHE = $NpmCache
$env:NPM_CONFIG_USERCONFIG = $NpmConfig
$env:Path = "$Root;$env:Path"

$npmRootSlash = $Root.Replace('\', '/')
$npmCacheSlash = $NpmCache.Replace('\', '/')
$npmConfigText = @"
prefix=$npmRootSlash
cache=$npmCacheSlash
update-notifier=false
audit=false
fund=false
"@
Set-Content -LiteralPath $NpmConfig -Value $npmConfigText -Encoding ASCII

# Retire seulement un paquet Codex incomplet; ne touche pas à Node ni à npm.
if ((Test-Path -LiteralPath $PackageDir -PathType Container) -and
    -not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    Remove-Item -LiteralPath $PackageDir -Recurse -Force
}

Write-Step "Installation visible de @openai/codex sur $Root"
Write-Host "La sortie complète est enregistrée dans : $NpmLog"

$npmArguments = @(
    $NpmCli,
    "install",
    "--global",
    "@openai/codex@latest",
    "--prefix=$npmRootSlash",
    "--cache=$npmCacheSlash",
    "--userconfig=$($NpmConfig.Replace('\', '/'))",
    "--no-audit",
    "--no-fund",
    "--loglevel=verbose"
)

# Appel direct de npm-cli.js avec node.exe : évite le comportement fragile de npm.cmd sous Windows PowerShell 5.1.
& $NodeExe @npmArguments 2>&1 | Tee-Object -FilePath $NpmLog
$npmExitCode = $LASTEXITCODE

if ($npmExitCode -ne 0) {
    throw "L'installation npm a échoué avec le code $npmExitCode. Journal : $NpmLog"
}

if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "npm a terminé sans créer le paquet attendu : $ManifestPath"
}

$manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$binRelativePath = if ($manifest.bin -is [string]) {
    [string]$manifest.bin
} else {
    [string]$manifest.bin.codex
}

if ([string]::IsNullOrWhiteSpace($binRelativePath)) {
    throw "Le manifeste @openai/codex ne déclare pas de commande codex."
}

$PackageEntry = Join-Path $PackageDir $binRelativePath
if (-not (Test-Path -LiteralPath $PackageEntry -PathType Leaf)) {
    throw "Le point d'entrée du paquet est absent : $PackageEntry"
}

Write-Step "Création vérifiée de la commande publique antmux"
foreach ($launcher in @(
    (Join-Path $Root "codex"),
    (Join-Path $Root "codex.cmd"),
    (Join-Path $Root "codex.ps1"),
    (Join-Path $Root "antmux.ps1")
)) {
    if (Test-Path -LiteralPath $launcher) {
        Remove-Item -LiteralPath $launcher -Force
    }
}

$cmdContent = @"
@echo off
setlocal
set "ANTMUX_ROOT=$Root"
set "CODEX_HOME=$Root"
set "NPM_CONFIG_PREFIX=$Root"
set "NPM_CONFIG_CACHE=$NpmCache"
set "NPM_CONFIG_USERCONFIG=$NpmConfig"
set "HOME=$Root"
set "XDG_CONFIG_HOME=$Root"
set "XDG_CACHE_HOME=$LocalAppDataDir"
set "APPDATA=$AppDataDir"
set "LOCALAPPDATA=$LocalAppDataDir"
set "TEMP=$TempDir"
set "TMP=$TempDir"
set "PATH=$Root;%PATH%"
"$NodeExe" "$PackageEntry" %*
set "ANTMUX_EXIT=%ERRORLEVEL%"
endlocal & exit /b %ANTMUX_EXIT%
"@
Set-Content -LiteralPath $AntmuxCmd -Value $cmdContent -Encoding ASCII

if (-not (Test-Path -LiteralPath $AntmuxCmd -PathType Leaf)) {
    throw "Le lanceur n'a pas été créé : $AntmuxCmd"
}

[Environment]::SetEnvironmentVariable("ANTMUX_ROOT", $Root, "User")
[Environment]::SetEnvironmentVariable("CODEX_HOME", $Root, "User")
[Environment]::SetEnvironmentVariable("NPM_CONFIG_PREFIX", $Root, "User")
[Environment]::SetEnvironmentVariable("NPM_CONFIG_CACHE", $NpmCache, "User")
[Environment]::SetEnvironmentVariable("NPM_CONFIG_USERCONFIG", $NpmConfig, "User")
Add-PathEntry -Entry $Root

Write-Step "Vérification finale"
& $env:ComSpec /d /c "`"$AntmuxCmd`" --version"
$verifyExitCode = $LASTEXITCODE
if ($verifyExitCode -ne 0) {
    throw "D:\antmux.cmd existe, mais sa vérification a échoué avec le code $verifyExitCode."
}

Write-Host ""
Write-Host "RÉPARATION TERMINÉE" -ForegroundColor Green
Write-Host "Lanceur : $AntmuxCmd"
Write-Host "Commande : antmux"
