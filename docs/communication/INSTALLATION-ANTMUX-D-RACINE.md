# Installation d’Antmux directement à la racine de `D:\`

## Demande de Brutus

> Fais-moi un script pour installer Codex CLI directement à la source du disque dur D. J'ai vu qu'il s'appelle antmux install a d: sans sous repertoir, a la source

## Résultat attendu

Le script `INSTALL-ANTMUX-D.ps1` installe l’environnement à partir de la racine `D:\`, sans créer de dossier principal `D:\Codex` ni `D:\Antmux`.

Après exécution, les éléments principaux sont notamment :

- `D:\node.exe`
- `D:\npm.cmd`
- `D:\antmux.cmd`
- `D:\node_modules\...`
- `D:\.npm-cache\...`
- `D:\ANTMUX-IDENTITY.md`
- `D:\antmux-install.log`

La commande publique est :

```powershell
antmux
```

Les lanceurs publics `codex`, `codex.cmd`, `codex.ps1` et tout ancien `antmux.ps1` sont supprimés après l’installation. Le lanceur conservé est `D:\antmux.cmd`, afin que la commande fonctionne dans PowerShell sans dépendre de la politique d’exécution des scripts `.ps1`.

## Prérequis protégés par le script

Le script refuse l’installation lorsque :

- `D:\` n’existe pas ou n’est pas prêt;
- `D:\` correspond au disque système Windows;
- le volume `D:\` ne porte pas le nom `Antmux`;
- Windows n’est pas en architecture x64 ou ARM64;
- la vérification SHA-256 de Node.js échoue;
- l’installation npm officielle échoue;
- la commande `antmux --version` échoue.

## Exécution

1. Enregistrer le script à cet emplacement :

```text
D:\INSTALL-ANTMUX-D.ps1
```

2. Ouvrir PowerShell.

3. Exécuter :

```powershell
Set-ExecutionPolicy -Scope Process Bypass
& "D:\INSTALL-ANTMUX-D.ps1"
```

4. Fermer puis rouvrir PowerShell.

5. Lancer Antmux :

```powershell
antmux
```

## Limite technique transparente

Le produit amont d’OpenAI et son paquet npm conservent nécessairement le nom technique `@openai/codex` dans `D:\node_modules`. Le script ne modifie pas le code source d’OpenAI. Il supprime toutefois les lanceurs publics nommés `codex` et expose la commande `antmux`.

Il n’existe aucun dossier principal `D:\Codex` ou `D:\Antmux`. Des répertoires techniques placés directement à la racine, notamment `D:\node_modules` et les caches cachés, restent nécessaires au fonctionnement.

## Script complet

```powershell
#requires -Version 5.1
<#
.SYNOPSIS
Installe l'environnement Antmux directement à la racine de D:\.

.DESCRIPTION
- Vérifie que D:\ existe, est prêt et porte le nom Antmux.
- Installe une version portable de Node.js directement dans D:\.
- Installe le paquet officiel @openai/codex avec le préfixe npm D:\.
- Supprime les lanceurs publics nommés codex.
- Crée D:\antmux.cmd comme commande publique.
- Redirige les données, caches et fichiers temporaires d'Antmux vers D:\.
- Ne crée aucun dossier principal D:\Codex ou D:\Antmux.

IMPORTANT
Le paquet amont conserve nécessairement son nom technique @openai/codex dans node_modules.
L'identité d'utilisation et la commande publique créées par ce script sont Antmux.
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
    $root = [System.IO.Path]::GetPathRoot($full)

    if ($full.TrimEnd([char]92) -ne $root.TrimEnd([char]92)) {
        throw "La cible doit être exactement la racine d'un disque. Reçu : $Path"
    }

    return $root
}

function Add-UserPathEntry {
    param([Parameter(Mandatory = $true)][string]$Entry)

    $current = [Environment]::GetEnvironmentVariable("Path", "User")
    $segments = @()

    if (-not [string]::IsNullOrWhiteSpace($current)) {
        $segments = @($current.Split(";", [System.StringSplitOptions]::RemoveEmptyEntries))
    }

    $normalized = $Entry.TrimEnd([char]92)
    $exists = $false

    foreach ($segment in $segments) {
        if ($segment.TrimEnd([char]92) -ieq $normalized) {
            $exists = $true
            break
        }
    }

    if (-not $exists) {
        $newPath = if ([string]::IsNullOrWhiteSpace($current)) {
            $Entry
        } else {
            "$Entry;$current"
        }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    }

    if ($env:Path.Split(";", [System.StringSplitOptions]::RemoveEmptyEntries) |
        Where-Object { $_.TrimEnd([char]92) -ieq $normalized }) {
        return
    }

    $env:Path = "$Entry;$env:Path"
}

function Set-HiddenDirectory {
    param([Parameter(Mandatory = $true)][string]$Path)

    New-Item -ItemType Directory -Force -Path $Path | Out-Null

    try {
        $item = Get-Item -LiteralPath $Path -Force
        $item.Attributes = $item.Attributes -bor [IO.FileAttributes]::Hidden
    } catch {
        Write-Warning "Impossible de masquer le dossier $Path. L'installation peut continuer."
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

function Get-NodeArchitecture {
    $architecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()

    switch ($architecture) {
        "X64"   { return "x64" }
        "Arm64" { return "arm64" }
        default { throw "Architecture Windows non prise en charge : $architecture" }
    }
}

$Root = Normalize-Root -Path $Root

Write-Step "Validation du disque $Root"

$drive = [System.IO.DriveInfo]::new($Root)
if (-not $drive.IsReady) {
    throw "Le disque $Root n'est pas prêt."
}

$systemRoot = [System.IO.Path]::GetPathRoot($env:SystemRoot)
if ($Root.TrimEnd([char]92) -ieq $systemRoot.TrimEnd([char]92)) {
    throw "Refus : $Root est le disque système Windows."
}

if (-not $SkipVolumeLabelCheck) {
    $label = $drive.VolumeLabel
    if ($label -ine "Antmux") {
        throw "Le disque $Root doit porter le nom Antmux. Nom actuel : '$label'."
    }
}

$TempDir       = Join-Path $Root ".antmux-temp"
$NpmCacheDir   = Join-Path $Root ".npm-cache"
$AppDataDir    = Join-Path $Root ".antmux-appdata"
$LocalDataDir  = Join-Path $Root ".antmux-localappdata"
$LogPath       = Join-Path $Root "antmux-install.log"
$NodeExe       = Join-Path $Root "node.exe"
$NpmCmd        = Join-Path $Root "npm.cmd"
$PackageDir     = Join-Path $Root "node_modules\@openai\codex"
$PackageManifest = Join-Path $PackageDir "package.json"
$AntmuxCmd      = Join-Path $Root "antmux.cmd"
$IdentityFile   = Join-Path $Root "ANTMUX-IDENTITY.md"

Set-HiddenDirectory -Path $TempDir
Set-HiddenDirectory -Path $NpmCacheDir
Set-HiddenDirectory -Path $AppDataDir
Set-HiddenDirectory -Path $LocalDataDir

$transcriptStarted = $false
try {
    Start-Transcript -Path $LogPath -Append | Out-Null
    $transcriptStarted = $true
} catch {
    Write-Warning "Le journal PowerShell n'a pas pu démarrer : $($_.Exception.Message)"
}

try {
    Write-Step "Détection de la version LTS actuelle de Node.js"

    $nodeArch = Get-NodeArchitecture
    $nodeIndex = Invoke-RestMethod -Uri "https://nodejs.org/dist/index.json"

    $fileKey = "win-$nodeArch-zip"
    $nodeRelease = $nodeIndex |
        Where-Object {
            $_.lts -and
            $_.files -and
            ($_.files -contains $fileKey)
        } |
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

    Invoke-WebRequest -Uri "$baseUrl/$zipName" -OutFile $zipPath
    Invoke-WebRequest -Uri "$baseUrl/SHASUMS256.txt" -OutFile $checksumsPath

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

    $extractedRoot = Get-ChildItem -LiteralPath $extractPath -Directory |
        Select-Object -First 1

    if ($null -eq $extractedRoot) {
        throw "Archive Node.js invalide : dossier racine introuvable."
    }

    Write-Step "Copie de Node.js directement dans $Root"

    foreach ($item in Get-ChildItem -LiteralPath $extractedRoot.FullName -Force) {
        $destination = Join-Path $Root $item.Name

        if ($item.PSIsContainer) {
            Copy-DirectoryMerged -Source $item.FullName -Destination $destination
        } else {
            Copy-Item -LiteralPath $item.FullName -Destination $destination -Force
        }
    }

    if (-not (Test-Path -LiteralPath $NodeExe -PathType Leaf)) {
        throw "node.exe n'a pas été installé à la racine de $Root."
    }

    if (-not (Test-Path -LiteralPath $NpmCmd -PathType Leaf)) {
        throw "npm.cmd n'a pas été installé à la racine de $Root."
    }

    $nodeInstalledVersion = (& $NodeExe --version).Trim()
    $npmInstalledVersion = (& $NpmCmd --version).Trim()

    Write-Host "Node.js : $nodeInstalledVersion"
    Write-Host "npm     : $npmInstalledVersion"

    Write-Step "Configuration npm entièrement sur $Root"

    $env:NPM_CONFIG_PREFIX = $Root
    $env:NPM_CONFIG_CACHE = $NpmCacheDir
    $env:CODEX_HOME = $Root
    $env:ANTMUX_ROOT = $Root
    $env:TEMP = $TempDir
    $env:TMP = $TempDir

    $npmRoot = $Root.Replace("\", "/")
    $npmCache = $NpmCacheDir.Replace("\", "/")

    $npmRc = @"
prefix=$npmRoot
cache=$npmCache
update-notifier=false
audit=false
fund=false
"@
    Set-Content -LiteralPath (Join-Path $Root ".npmrc") -Value $npmRc -Encoding UTF8

    Write-Step "Installation du paquet officiel OpenAI dans la racine npm de $Root"

    & $NpmCmd `
        "install" `
        "--global" `
        "@openai/codex@latest" `
        "--prefix=$npmRoot" `
        "--cache=$npmCache" `
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

    Write-Step "Suppression des lanceurs publics nommés codex"

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

    Write-Step "Création de la commande publique antmux"

    $cmdContent = @"
@echo off
setlocal
set "ANTMUX_ROOT=$Root"
set "CODEX_HOME=$Root"
set "NPM_CONFIG_PREFIX=$Root"
set "NPM_CONFIG_CACHE=$NpmCacheDir"
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
    Write-Host ""
    Write-Host "Ferme puis rouvre PowerShell avant le premier lancement normal."
    Write-Host "Ensuite, tape : antmux"
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

```
