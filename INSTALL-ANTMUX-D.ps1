#requires -Version 5.1
<#+
.SYNOPSIS
Installe Codex CLI directement comme D:\antmux.exe.

.DESCRIPTION
Méthode volontairement simple :
1. télécharge le paquet Windows officiel OpenAI;
2. vérifie son SHA-256;
3. extrait ses fichiers directement à la racine de D:\;
4. renomme codex.exe en antmux.exe;
5. vérifie antmux.exe --version;
6. nettoie les restes Node/npm des essais précédents.

Aucun Node.js. Aucun npm. Aucun lanceur .cmd.
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

function Get-WindowsTarget {
    if (-not [Environment]::Is64BitOperatingSystem) {
        throw "Antmux exige Windows 64 bits."
    }

    $architecture = $env:PROCESSOR_ARCHITEW6432
    if ([string]::IsNullOrWhiteSpace($architecture)) {
        $architecture = $env:PROCESSOR_ARCHITECTURE
    }

    switch -Regex ([string]$architecture) {
        '^(AMD64|x86_64)$' { return "x86_64-pc-windows-msvc" }
        '^ARM64$'          { return "aarch64-pc-windows-msvc" }
        default            { throw "Architecture Windows non prise en charge : '$architecture'." }
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

function Remove-OldNodeAttempt {
    param([Parameter(Mandatory = $true)][string]$DriveRoot)

    foreach ($relativePath in @(
        "node.exe",
        "npm",
        "npm.cmd",
        "npx",
        "npx.cmd",
        "corepack",
        "corepack.cmd",
        "node_modules",
        ".npmrc",
        ".npm-cache",
        ".antmux-appdata",
        ".antmux-localappdata",
        "antmux-npm-install.log",
        "REPAIR-ANTMUX-D.ps1",
        "codex",
        "codex.cmd",
        "codex.ps1",
        "antmux.cmd",
        "antmux.ps1"
    )) {
        $path = Join-Path $DriveRoot $relativePath
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue
        }
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

$target = Get-WindowsTarget
$assetName = "codex-package-$target.tar.gz"
$releaseApi = "https://api.github.com/repos/openai/codex/releases/latest"
$tempDir = Join-Path $Root ".antmux-install-temp"
$archivePath = Join-Path $tempDir $assetName
$extractDir = Join-Path $tempDir "extract"
$antmuxExe = Join-Path $Root "antmux.exe"

if (Test-Path -LiteralPath $tempDir) {
    Remove-Item -LiteralPath $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $extractDir | Out-Null

try {
    Write-Step "Recherche de la dernière version officielle OpenAI"
    $release = Invoke-RestMethod -UseBasicParsing -Uri $releaseApi -Headers @{ "User-Agent" = "Antmux-Installer" }
    $asset = $release.assets | Where-Object { $_.name -eq $assetName } | Select-Object -First 1

    if ($null -eq $asset) {
        throw "Le paquet officiel attendu est absent : $assetName"
    }

    Write-Host "Version : $($release.tag_name)"
    Write-Host "Paquet : $assetName"

    Write-Step "Téléchargement sur le disque Antmux"
    Invoke-WebRequest -UseBasicParsing -Uri $asset.browser_download_url -OutFile $archivePath

    $digestProperty = $asset.PSObject.Properties["digest"]
    if ($null -eq $digestProperty -or [string]::IsNullOrWhiteSpace([string]$digestProperty.Value)) {
        throw "GitHub n'a pas fourni le SHA-256 du paquet officiel. Installation refusée."
    }

    $digestText = [string]$digestProperty.Value
    if ($digestText -notmatch '^sha256:([0-9a-fA-F]{64})$') {
        throw "Format SHA-256 officiel invalide : $digestText"
    }

    Write-Step "Vérification SHA-256"
    $expectedHash = $matches[1].ToLowerInvariant()
    $actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) {
        throw "Le téléchargement ne correspond pas au paquet officiel OpenAI."
    }

    Write-Step "Extraction du paquet officiel"
    $tar = Get-Command tar.exe -ErrorAction Stop
    & $tar.Source -xzf $archivePath -C $extractDir
    if ($LASTEXITCODE -ne 0) {
        throw "L'extraction du paquet officiel a échoué."
    }

    $sourceCodex = Get-ChildItem -LiteralPath $extractDir -Recurse -File -Filter "codex.exe" |
        Select-Object -First 1

    if ($null -eq $sourceCodex) {
        throw "codex.exe est absent du paquet officiel."
    }

    $sourceBin = $sourceCodex.Directory.FullName

    Write-Step "Copie directe à la racine de $Root"
    foreach ($item in Get-ChildItem -LiteralPath $sourceBin -Force) {
        if ($item.FullName -eq $sourceCodex.FullName) {
            continue
        }

        Copy-Item -LiteralPath $item.FullName -Destination (Join-Path $Root $item.Name) -Recurse -Force
    }

    Copy-Item -LiteralPath $sourceCodex.FullName -Destination $antmuxExe -Force

    if (-not (Test-Path -LiteralPath $antmuxExe -PathType Leaf)) {
        throw "Le fichier $antmuxExe n'a pas été créé."
    }

    $env:ANTMUX_ROOT = $Root
    $env:CODEX_HOME = $Root
    [Environment]::SetEnvironmentVariable("ANTMUX_ROOT", $Root, "User")
    [Environment]::SetEnvironmentVariable("CODEX_HOME", $Root, "User")
    Add-PathEntry -Entry $Root

    Write-Step "Vérification réelle"
    & $antmuxExe --version
    if ($LASTEXITCODE -ne 0) {
        throw "antmux.exe existe, mais ne démarre pas correctement."
    }

    Write-Step "Nettoyage des anciens essais Node/npm"
    Remove-OldNodeAttempt -DriveRoot $Root

    if (-not (Test-Path -LiteralPath $antmuxExe -PathType Leaf)) {
        throw "Erreur interne : antmux.exe a disparu pendant le nettoyage."
    }

    Write-Host ""
    Write-Host "INSTALLATION RÉUSSIE" -ForegroundColor Green
    Write-Host "Binaire : $antmuxExe"
    Write-Host "Commande : antmux"
}
finally {
    if (Test-Path -LiteralPath $tempDir) {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
