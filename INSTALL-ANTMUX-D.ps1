#requires -Version 5.1
<#+
.SYNOPSIS
Installe le binaire Windows officiel de Codex directement comme D:\antmux.exe.

.DESCRIPTION
Aucun Node.js. Aucun npm. Aucun lanceur .cmd.
Le script télécharge la dernière version officielle depuis openai/codex,
vérifie son SHA-256 lorsqu'il est publié par GitHub, extrait le binaire,
le renomme antmux.exe, vérifie son fonctionnement, puis nettoie les restes
de l'ancienne tentative Node/npm.
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

    $oldItems = @(
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
    )

    foreach ($relativePath in $oldItems) {
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
$AntmuxExe = Join-Path $Root "antmux.exe"
$TempDir = Join-Path $Root ".antmux-install-temp"
$ReleaseApi = "https://api.github.com/repos/openai/codex/releases/latest"

if (Test-Path -LiteralPath $TempDir) {
    Remove-Item -LiteralPath $TempDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $TempDir | Out-Null

try {
    Write-Step "Recherche de la dernière version officielle OpenAI"
    $release = Invoke-RestMethod -UseBasicParsing -Uri $ReleaseApi -Headers @{ "User-Agent" = "Antmux-Installer" }
    Write-Host "Version officielle : $($release.tag_name)"
    Write-Host "Architecture : $target"

    $candidateAssets = @($release.assets | Where-Object {
        $_.name -match [regex]::Escape($target) -and
        $_.name -match '\.(exe|zip|tar\.gz)$' -and
        $_.name -notmatch 'npm'
    })

    if ($candidateAssets.Count -eq 0) {
        throw "Aucun binaire Windows officiel trouvé pour $target dans la version $($release.tag_name)."
    }

    $asset = $candidateAssets |
        Sort-Object @{ Expression = {
            if ($_.name -eq "codex-$target.exe") { 0 }
            elseif ($_.name -eq "codex-$target.zip") { 1 }
            elseif ($_.name -eq "codex-$target.tar.gz") { 2 }
            elseif ($_.name -eq "codex-package-$target.tar.gz") { 3 }
            else { 9 }
        }} |
        Select-Object -First 1

    Write-Host "Fichier officiel sélectionné : $($asset.name)"
    $downloadPath = Join-Path $TempDir $asset.name

    Write-Step "Téléchargement du binaire officiel sur $Root"
    Invoke-WebRequest -UseBasicParsing -Uri $asset.browser_download_url -OutFile $downloadPath

    $digestProperty = $asset.PSObject.Properties["digest"]
    if ($null -ne $digestProperty -and -not [string]::IsNullOrWhiteSpace([string]$digestProperty.Value)) {
        $digestText = [string]$digestProperty.Value
        if ($digestText -match '^sha256:([0-9a-fA-F]{64})$') {
            Write-Step "Vérification SHA-256"
            $expectedHash = $matches[1].ToLowerInvariant()
            $actualHash = (Get-FileHash -LiteralPath $downloadPath -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($actualHash -ne $expectedHash) {
                throw "Le SHA-256 du téléchargement ne correspond pas au fichier officiel."
            }
        }
    }

    $extractDir = Join-Path $TempDir "extract"
    New-Item -ItemType Directory -Force -Path $extractDir | Out-Null

    if ($asset.name -match '\.exe$') {
        $sourceExe = $downloadPath
    } elseif ($asset.name -match '\.zip$') {
        Write-Step "Extraction de l'archive officielle"
        Expand-Archive -LiteralPath $downloadPath -DestinationPath $extractDir -Force
        $sourceExe = $null
    } elseif ($asset.name -match '\.tar\.gz$') {
        Write-Step "Extraction de l'archive officielle"
        $tar = Get-Command tar.exe -ErrorAction Stop
        & $tar.Source -xzf $downloadPath -C $extractDir
        if ($LASTEXITCODE -ne 0) {
            throw "L'extraction de l'archive officielle a échoué."
        }
        $sourceExe = $null
    } else {
        throw "Format officiel non pris en charge : $($asset.name)"
    }

    if ($null -eq $sourceExe) {
        $allExecutables = @(Get-ChildItem -LiteralPath $extractDir -Recurse -File -Filter "*.exe")
        $sourceExe = $allExecutables | Where-Object { $_.Name -ieq "codex.exe" } | Select-Object -First 1

        if ($null -eq $sourceExe) {
            $sourceExe = $allExecutables |
                Where-Object {
                    $_.Name -match '^codex.*\.exe$' -and
                    $_.Name -notmatch 'command-runner|sandbox|setup'
                } |
                Select-Object -First 1
        }
    }

    if ($null -eq $sourceExe -or -not (Test-Path -LiteralPath $sourceExe.FullName -PathType Leaf)) {
        throw "Le véritable exécutable Codex est introuvable dans le fichier officiel."
    }

    Write-Step "Installation directe comme $AntmuxExe"

    if ($sourceExe -is [System.IO.FileInfo]) {
        $sourceDirectory = $sourceExe.Directory.FullName
        foreach ($item in Get-ChildItem -LiteralPath $sourceDirectory -Force) {
            if ($item.FullName -eq $sourceExe.FullName) {
                continue
            }

            $destination = Join-Path $Root $item.Name
            Copy-Item -LiteralPath $item.FullName -Destination $destination -Recurse -Force
        }
        Copy-Item -LiteralPath $sourceExe.FullName -Destination $AntmuxExe -Force
    } else {
        Copy-Item -LiteralPath $sourceExe -Destination $AntmuxExe -Force
    }

    if (-not (Test-Path -LiteralPath $AntmuxExe -PathType Leaf)) {
        throw "Le fichier $AntmuxExe n'a pas été créé."
    }

    $env:ANTMUX_ROOT = $Root
    $env:CODEX_HOME = $Root
    [Environment]::SetEnvironmentVariable("ANTMUX_ROOT", $Root, "User")
    [Environment]::SetEnvironmentVariable("CODEX_HOME", $Root, "User")
    Add-PathEntry -Entry $Root

    Write-Step "Vérification réelle avant nettoyage"
    & $AntmuxExe --version
    if ($LASTEXITCODE -ne 0) {
        throw "Le binaire officiel renommé Antmux ne démarre pas."
    }

    Write-Step "Nettoyage des anciennes tentatives Node/npm"
    Remove-OldNodeAttempt -DriveRoot $Root

    # Le nettoyage ne doit jamais supprimer le nouveau binaire.
    if (-not (Test-Path -LiteralPath $AntmuxExe -PathType Leaf)) {
        throw "Erreur interne : antmux.exe a disparu pendant le nettoyage."
    }

    Write-Host ""
    Write-Host "INSTALLATION RÉUSSIE" -ForegroundColor Green
    Write-Host "Binaire : $AntmuxExe"
    Write-Host "Commande : antmux"
    Write-Host "Version : $($release.tag_name)"
}
finally {
    if (Test-Path -LiteralPath $TempDir) {
        Remove-Item -LiteralPath $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
