#requires -Version 5.1
<#
.SYNOPSIS
Installe Antmux directement à la racine de D:\.

.DESCRIPTION
- Compatible avec Windows PowerShell 5.1 et PowerShell 7+.
- Vérifie que D:\ est un disque prêt, non système, nommé Antmux.
- Installe Node.js portable directement à la racine de D:\.
- Installe le paquet officiel @openai/codex avec le préfixe npm D:\.
- Garde caches, configuration, données et temporaires sur D:\.
- Supprime les lanceurs publics codex et crée D:\antmux.cmd.
- Ne crée aucun dossier principal D:\Codex ou D:\Antmux.

Le paquet amont conserve son nom technique @openai/codex dans node_modules.
La commande publique créée par ce script est antmux.
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
        throw "La cible doit être exactement la racine d'un disque. Reçu : $Path"
    }

    return $driveRoot
}

function Get-NodeArchitecture {
    if (-not [Environment]::Is64BitOperatingSystem) {
        throw "Antmux exige une version 64 bits de Windows."
    }

    # Compatible Windows PowerShell 5.1 : ne dépend pas de RuntimeInformation.OSArchitecture.
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

    if ([string]$reportedArchitecture -match 'ARM') {
        return "arm64"
    }
    if ([string]$reportedArchitecture -match '64') {
        return "x64"
    }

    throw "Architecture Windows non prise en charge ou indétectable : '$architecture'."
}

function Add-UserPathEntry {
    param([Parameter(Mandatory = $true)][string]$Entry)

    $current = [Environment]::GetEnvironmentVariable("Path", "User")
    $segments = @()
    if (-not [string]::IsNullOrWhiteSpace($current)) {
        $segments = @($current.Split(";", [System.StringSplitOptions]::RemoveEmptyEntries))
    }

    $normalized = $Entry.TrimEnd([char]92)
    $alreadyPresent = $false
    foreach ($segment in $segments) {
        if ($segment.TrimEnd([char]92) -ieq $normalized) {
            $alreadyPresent = $true
            break
        }
    }

    if (-not $alreadyPresent) {
        $newPath = if ([string]::IsNullOrWhiteSpace($current)) {
            $Entry
        } else {
            "$Entry;$current"
        }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    }

    $processSegments = @($env:Path.Split(";", [System.StringSplitOptions]::RemoveEmptyEntries))
    $presentInProcess = $false
    foreach ($segment in $processSegments) {
        if ($segment.TrimEnd([char]92) -ieq $normalized) {
            $presentInProcess = $true
            break
        }
    }

    if (-not $presentInProcess) {
        $env:Path = "$Entry;$env:Path"
    }
}

function Ensure-HiddenDirectory {
    param([Parameter(Mandatory = $true)][string]$Path)

    New-Item -ItemType Directory -Force -Path $Path | Out-Null
    try {
        $item = Get-Item -LiteralPath $Path -Force
        $item.Attributes = $item.Attributes -bor [IO.FileAttributes]::Hidden
    } catch {
        Write-Warning "Impossible de masquer le dossier $Path. L'installation continue."
    }
}

function Copy-DirectoryMerged {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    foreach ($child in Get-ChildItem -LiteralPath $Source -Force) {
        $target = Join-Path $Destination $child.Name
        if ($child.PSIsContainer) {
            Copy-DirectoryMerged -Source $child.FullName -Destination $target
        } else {
            Copy-Item -LiteralPath $child.FullName -Destination $target -Force
        }
    }
}

$Root = Normalize-Root -Path $Root
Write-Step "Validation du disque $Root"

$drive = New-Object -TypeName System.IO.DriveInfo -ArgumentList $Root
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

$TempDir         = Join-Path $Root ".antmux-temp"
$NpmCacheDir     = Join-Path $Root ".npm-cache"
$AppDataDir      = Join-Path $Root ".antmux-appdata"
$LocalDataDir    = Join-Path $Root ".antmux-localappdata"
$NpmConfigPath   = Join-Path $Root ".npmrc"
$LogPath         = Join-Path $Root "antmux-install.log"
$NodeExe         = Join-Path $Root "node.exe"
$NpmCmd          = Join-Path $Root "npm.cmd"
$PackageDir      = Join-Path $Root "node_modules\@openai\codex"
$PackageManifest = Join-Path $PackageDir "package.json"
$AntmuxCmd       = Join-Path $Root "antmux.cmd"
$IdentityFile    = Join-Path $Root "ANTMUX-IDENTITY.md"

foreach ($directory in @($TempDir, $NpmCacheDir, $AppDataDir, $LocalDataDir)) {
    Ensure-HiddenDirectory -Path $directory
}

# Toutes les écritures temporaires et applicatives de ce processus restent sur D:\.
$env:ANTMUX_ROOT = $Root
$env:CODEX_HOME = $Root
$env:HOME = $Root
$env:XDG_CONFIG_HOME = $Root
$env:XDG_CACHE_HOME = $LocalDataDir
$env:APPDATA = $AppDataDir
$env:LOCALAPPDATA = $LocalDataDir
$env:TEMP = $TempDir
$env:TMP = $TempDir
$env:NPM_CONFIG_PREFIX = $Root
$env:NPM_CONFIG_CACHE = $NpmCacheDir
$env:NPM_CONFIG_USERCONFIG = $NpmConfigPath
$env:Path = "$Root;$env:Path"

$transcriptStarted = $false
try {
    Start-Transcript -Path $LogPath -Append | Out-Null
    $transcriptStarted = $true
} catch {
    Write-Warning "Le journal PowerShell n'a pas pu démarrer : $($_.Exception.Message)"
}

try {
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

    Write-Step "Téléchargement de Node.js $nodeVersion vers le disque Antmux"
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

    if (-not (Test-Path -LiteralPath $NodeExe -PathType Leaf)) {
        throw "node.exe n'a pas été installé à la racine de $Root."
    }
    if (-not (Test-Path -LiteralPath $NpmCmd -PathType Leaf)) {
        throw "npm.cmd n'a pas été installé à la racine de $Root."
    }

    Write-Host "Node.js : $((& $NodeExe --version).Trim())"
    Write-Host "npm     : $((& $NpmCmd --version).Trim())"

    $npmRoot = $Root.Replace("\", "/")
    $npmCache = $NpmCacheDir.Replace("\", "/")
    $npmRc = @"
prefix=$npmRoot
cache=$npmCache
update-notifier=false
audit=false
fund=false
"@
    Set-Content -LiteralPath $NpmConfigPath -Value $npmRc -Encoding ASCII

    Write-Step "Installation du paquet officiel OpenAI à la racine npm de $Root"
    & $NpmCmd `
        "install" `
        "--global" `
        "@openai/codex@latest" `
        "--prefix=$npmRoot" `
        "--cache=$npmCache" `
        "--userconfig=$($NpmConfigPath.Replace('\', '/'))" `
        "--no-audit" `
        "--no-fund"

    if ($LASTEXITCODE -ne 0) {
        throw "npm a retourné le code d'erreur $LASTEXITCODE."
    }

    if (-not (Test-Path -LiteralPath $PackageManifest -PathType Leaf)) {
        throw "Le manifeste du paquet officiel n'a pas été trouvé : $PackageManifest"
    }

    $manifest = Get-Content -LiteralPath $PackageManifest -Raw | ConvertFrom-Json
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
        throw "Le point d'entrée officiel n'a pas été trouvé : $PackageEntry"
    }

    Write-Step "Création de la commande publique antmux"
    foreach ($legacyLauncher in @(
        (Join-Path $Root "codex"),
        (Join-Path $Root "codex.cmd"),
        (Join-Path $Root "codex.ps1"),
        (Join-Path $Root "antmux.ps1")
    )) {
        if (Test-Path -LiteralPath $legacyLauncher) {
            Remove-Item -LiteralPath $legacyLauncher -Force
        }
    }

    $cmdContent = @"
@echo off
setlocal
set "ANTMUX_ROOT=$Root"
set "CODEX_HOME=$Root"
set "NPM_CONFIG_PREFIX=$Root"
set "NPM_CONFIG_CACHE=$NpmCacheDir"
set "NPM_CONFIG_USERCONFIG=$NpmConfigPath"
set "HOME=$Root"
set "XDG_CONFIG_HOME=$Root"
set "XDG_CACHE_HOME=$LocalDataDir"
set "APPDATA=$AppDataDir"
set "LOCALAPPDATA=$LocalDataDir"
set "TEMP=$TempDir"
set "TMP=$TempDir"
set "PATH=$Root;%PATH%"
"$NodeExe" "$PackageEntry" %*
set "ANTMUX_EXIT=%ERRORLEVEL%"
endlocal & exit /b %ANTMUX_EXIT%
"@
    Set-Content -LiteralPath $AntmuxCmd -Value $cmdContent -Encoding ASCII

    $identityContent = @"
# Antmux

- Disque : $Root
- Nom du volume exigé : Antmux
- Commande publique : ``antmux``
- Lanceur public : ``$AntmuxCmd``
- Données et configuration : directement sur ``$Root``
- Cache npm : ``$NpmCacheDir``
- Première travailleuse déclarée : **Linuxia — Reine**
- Paquet technique amont : ``@openai/codex``
- Règle absolue : aucun fichier du projet ne doit être installé volontairement hors du disque Antmux.
"@
    Set-Content -LiteralPath $IdentityFile -Value $identityContent -Encoding UTF8

    Write-Step "Enregistrement des variables utilisateur"
    [Environment]::SetEnvironmentVariable("ANTMUX_ROOT", $Root, "User")
    [Environment]::SetEnvironmentVariable("CODEX_HOME", $Root, "User")
    [Environment]::SetEnvironmentVariable("NPM_CONFIG_PREFIX", $Root, "User")
    [Environment]::SetEnvironmentVariable("NPM_CONFIG_CACHE", $NpmCacheDir, "User")
    [Environment]::SetEnvironmentVariable("NPM_CONFIG_USERCONFIG", $NpmConfigPath, "User")
    Add-UserPathEntry -Entry $Root

    Write-Step "Vérification finale"
    & $AntmuxCmd --version
    if ($LASTEXITCODE -ne 0) {
        throw "La commande antmux --version a échoué."
    }

    Write-Host ""
    Write-Host "INSTALLATION TERMINÉE" -ForegroundColor Green
    Write-Host "Commande : antmux"
    Write-Host "Emplacement : $Root"
    Write-Host "Journal : $LogPath"
    Write-Host "Tu peux maintenant exécuter : antmux"
}
finally {
    if ($transcriptStarted) {
        Stop-Transcript | Out-Null
    }

    if (Test-Path -LiteralPath $TempDir) {
        Get-ChildItem -LiteralPath $TempDir -Force -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
}
