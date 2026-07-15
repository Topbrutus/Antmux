#requires -Version 5.1
<#+
.SYNOPSIS
Installe ou répare Antmux directement à la racine du disque D:\.

.DESCRIPTION
- Vérifie que la cible est une racine de disque non système nommée Antmux.
- Installe Node.js portable directement à la racine si nécessaire.
- Installe @openai/codex en appelant npm-cli.js directement avec node.exe.
- Conserve caches, configuration, données et temporaires sur le disque Antmux.
- Crée uniquement la commande publique D:\antmux.cmd.
#>

[CmdletBinding()]
param(
    [string]$Root = "D:\",
    [switch]$SkipVolumeLabelCheck
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

function Get-NodeArchitecture {
    if (-not [Environment]::Is64BitOperatingSystem) {
        throw "Antmux exige une version 64 bits de Windows."
    }

    $architecture = $env:PROCESSOR_ARCHITEW6432
    if ([string]::IsNullOrWhiteSpace($architecture)) {
        $architecture = $env:PROCESSOR_ARCHITECTURE
    }

    switch -Regex ([string]$architecture) {
        '^(AMD64|x86_64)$' { return "x64" }
        '^ARM64$'          { return "arm64" }
    }

    $reportedArchitecture = $null
    try {
        $reportedArchitecture = (Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop).OSArchitecture
    } catch {
        try {
            $reportedArchitecture = (Get-WmiObject -Class Win32_OperatingSystem -ErrorAction Stop).OSArchitecture
        } catch {
            $reportedArchitecture = $null
        }
    }

    if ([string]$reportedArchitecture -match 'ARM') { return "arm64" }
    if ([string]$reportedArchitecture -match '64')  { return "x64" }

    throw "Architecture Windows non prise en charge ou indétectable : '$architecture'."
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Copy-DirectoryMerged {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    Ensure-Directory -Path $Destination
    foreach ($child in Get-ChildItem -LiteralPath $Source -Force) {
        $target = Join-Path $Destination $child.Name
        if ($child.PSIsContainer) {
            Copy-DirectoryMerged -Source $child.FullName -Destination $target
        } else {
            Copy-Item -LiteralPath $child.FullName -Destination $target -Force
        }
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
$drive = [System.IO.DriveInfo]::new($Root)
if (-not $drive.IsReady) {
    throw "Le disque $Root n'est pas prêt."
}

$systemRoot = [System.IO.Path]::GetPathRoot($env:SystemRoot)
if ($Root.TrimEnd([char]92) -ieq $systemRoot.TrimEnd([char]92)) {
    throw "Refus : $Root est le disque système Windows."
}

if (-not $SkipVolumeLabelCheck -and $drive.VolumeLabel -ine "Antmux") {
    throw "Le disque $Root doit porter le nom Antmux. Nom actuel : '$($drive.VolumeLabel)'."
}

$NodeExe = Join-Path $Root "node.exe"
$NpmCli = Join-Path $Root "node_modules\npm\bin\npm-cli.js"
$PackageDir = Join-Path $Root "node_modules\@openai\codex"
$ManifestPath = Join-Path $PackageDir "package.json"
$AntmuxCmd = Join-Path $Root "antmux.cmd"
$IdentityFile = Join-Path $Root "ANTMUX-IDENTITY.md"
$NpmConfig = Join-Path $Root ".npmrc"
$NpmCache = Join-Path $Root ".npm-cache"
$TempDir = Join-Path $Root ".antmux-temp"
$AppDataDir = Join-Path $Root ".antmux-appdata"
$LocalAppDataDir = Join-Path $Root ".antmux-localappdata"
$NpmLog = Join-Path $Root "antmux-npm-install.log"

foreach ($directory in @($NpmCache, $TempDir, $AppDataDir, $LocalAppDataDir)) {
    Ensure-Directory -Path $directory
}

# Toutes les écritures de ce processus restent sur le disque Antmux.
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

if (-not (Test-Path -LiteralPath $NodeExe -PathType Leaf) -or
    -not (Test-Path -LiteralPath $NpmCli -PathType Leaf)) {

    Write-Step "Détection de l'architecture Windows"
    $nodeArch = Get-NodeArchitecture
    Write-Host "Architecture Node.js sélectionnée : $nodeArch"

    Write-Step "Détection de la version LTS actuelle de Node.js"
    $nodeIndex = Invoke-RestMethod -UseBasicParsing -Uri "https://nodejs.org/dist/index.json"
    $fileKey = "win-$nodeArch-zip"
    $nodeRelease = $nodeIndex |
        Where-Object { $_.lts -and $_.files -and ($_.files -contains $fileKey) } |
        Select-Object -First 1

    if ($null -eq $nodeRelease) {
        throw "Aucune version LTS de Node.js compatible avec Windows $nodeArch n'a été trouvée."
    }

    $nodeVersion = [string]$nodeRelease.version
    $zipName = "node-$nodeVersion-win-$nodeArch.zip"
    $baseUrl = "https://nodejs.org/dist/$nodeVersion"
    $zipPath = Join-Path $TempDir $zipName
    $checksumsPath = Join-Path $TempDir "SHASUMS256.txt"
    $extractPath = Join-Path $TempDir "node-extract"

    Write-Step "Téléchargement de Node.js $nodeVersion sur le disque Antmux"
    Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/$zipName" -OutFile $zipPath
    Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/SHASUMS256.txt" -OutFile $checksumsPath

    $checksumLine = Get-Content -LiteralPath $checksumsPath |
        Where-Object { $_ -match ("\s+" + [regex]::Escape($zipName) + "$") } |
        Select-Object -First 1

    if ([string]::IsNullOrWhiteSpace($checksumLine)) {
        throw "Somme SHA-256 introuvable pour $zipName."
    }

    $expectedHash = ($checksumLine -split "\s+")[0].ToLowerInvariant()
    $actualHash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) {
        throw "Échec de vérification SHA-256 de Node.js."
    }

    if (Test-Path -LiteralPath $extractPath) {
        Remove-Item -LiteralPath $extractPath -Recurse -Force
    }
    Expand-Archive -LiteralPath $zipPath -DestinationPath $extractPath -Force

    $extractedRoot = Get-ChildItem -LiteralPath $extractPath -Directory | Select-Object -First 1
    if ($null -eq $extractedRoot) {
        throw "Archive Node.js invalide : dossier racine introuvable."
    }

    Write-Step "Installation de Node.js directement à la racine de $Root"
    $rootFilePattern = '^(node\.exe|npm|npm\.cmd|npx|npx\.cmd|corepack|corepack\.cmd)$'
    foreach ($file in Get-ChildItem -LiteralPath $extractedRoot.FullName -File -Force) {
        if ($file.Name -match $rootFilePattern) {
            Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $Root $file.Name) -Force
        }
    }

    $sourceNodeModules = Join-Path $extractedRoot.FullName "node_modules"
    if (-not (Test-Path -LiteralPath $sourceNodeModules -PathType Container)) {
        throw "Le dossier node_modules de Node.js est introuvable dans l'archive."
    }
    Copy-DirectoryMerged -Source $sourceNodeModules -Destination (Join-Path $Root "node_modules")
}

if (-not (Test-Path -LiteralPath $NodeExe -PathType Leaf)) {
    throw "node.exe est absent après l'installation : $NodeExe"
}
if (-not (Test-Path -LiteralPath $NpmCli -PathType Leaf)) {
    throw "npm-cli.js est absent après l'installation : $NpmCli"
}

Write-Host "Node.js : $((& $NodeExe --version).Trim())"

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

if ((Test-Path -LiteralPath $PackageDir -PathType Container) -and
    -not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    Remove-Item -LiteralPath $PackageDir -Recurse -Force
}

Write-Step "Installation visible du paquet officiel OpenAI sur $Root"
Write-Host "Journal npm : $NpmLog"

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

# Appel direct : ne dépend pas du comportement de npm.cmd dans Windows PowerShell 5.1.
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

Write-Step "Création vérifiée de la commande publique antmux"
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

$identityContent = @"
# Antmux

- Disque : $Root
- Commande publique : ``antmux``
- Lanceur : ``$AntmuxCmd``
- Configuration et caches : sur ``$Root``
- Première travailleuse : **Linuxia — Reine**
- Paquet technique amont : ``@openai/codex``
"@
Set-Content -LiteralPath $IdentityFile -Value $identityContent -Encoding UTF8

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

if (Test-Path -LiteralPath $TempDir) {
    Get-ChildItem -LiteralPath $TempDir -Force -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "INSTALLATION TERMINÉE" -ForegroundColor Green
Write-Host "Commande : antmux"
Write-Host "Lanceur : $AntmuxCmd"
Write-Host "Journal npm : $NpmLog"
