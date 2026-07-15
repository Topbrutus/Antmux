#requires -Version 5.1

[CmdletBinding()]
param([string]$Root)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

if ([string]::IsNullOrWhiteSpace($Root)) {
    if (-not [string]::IsNullOrWhiteSpace($MyInvocation.MyCommand.Path)) {
        $Root = [System.IO.Path]::GetPathRoot($MyInvocation.MyCommand.Path)
    }
    else {
        $Root = "D:\"
    }
}

$Root = [System.IO.Path]::GetFullPath($Root)
$driveRoot = [System.IO.Path]::GetPathRoot($Root)
$drive = New-Object System.IO.DriveInfo($driveRoot)

if (-not $drive.IsReady) {
    throw "The target drive is not ready: $driveRoot"
}
if ($drive.VolumeLabel -ine "Antmux") {
    throw "The target drive must be named Antmux. Current label: '$($drive.VolumeLabel)'."
}

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
}
catch {
    # Keep the platform default when TLS 1.2 cannot be selected explicitly.
}

$baseUrl = "https://raw.githubusercontent.com/Topbrutus/Antmux/main"
$moduleDirectory = Join-Path $Root "modules\jules"
$configDirectory = Join-Path $Root "config"
$modulePath = Join-Path $moduleDirectory "Jules.SummaryPublisher.psm1"
$commandPath = Join-Path $moduleDirectory "Send-AntmuxSummary.ps1"
$configPath = Join-Path $configDirectory "jules-summary-publisher.json"
$backupStamp = Get-Date -Format "yyyyMMdd-HHmmss"

New-Item -ItemType Directory -Force -Path $moduleDirectory | Out-Null
New-Item -ItemType Directory -Force -Path $configDirectory | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root "communication\resumes") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root ".antmux-git") | Out-Null

$downloads = @(
    [pscustomobject]@{
        Url = "$baseUrl/modules/jules/Jules.SummaryPublisher.psm1"
        Path = $modulePath
    },
    [pscustomobject]@{
        Url = "$baseUrl/modules/jules/Send-AntmuxSummary.ps1"
        Path = $commandPath
    },
    [pscustomobject]@{
        Url = "$baseUrl/config/jules-summary-publisher.json"
        Path = $configPath
    }
)

foreach ($download in $downloads) {
    if (Test-Path -LiteralPath $download.Path -PathType Leaf) {
        $leaf = [System.IO.Path]::GetFileName($download.Path)
        $backup = Join-Path ([System.IO.Path]::GetDirectoryName($download.Path)) "$leaf.backup.$backupStamp"
        Copy-Item -LiteralPath $download.Path -Destination $backup -Force
        Write-Host "Backup created: $backup"
    }

    $temporary = "$($download.Path).download"
    Invoke-WebRequest -UseBasicParsing -Uri $download.Url -OutFile $temporary
    Move-Item -LiteralPath $temporary -Destination $download.Path -Force
}

$null = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json

foreach ($scriptPath in @($modulePath, $commandPath)) {
    $tokens = $null
    $errors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile(
        $scriptPath,
        [ref]$tokens,
        [ref]$errors
    )
    if ($errors.Count -gt 0) {
        throw "PowerShell syntax error in $scriptPath : $($errors[0].Message)"
    }
}

Import-Module -Name $modulePath -Force

Write-Host ""
Write-Host "JULES SUMMARY PUBLISHER INSTALLED" -ForegroundColor Green
Write-Host "Root    : $Root"
Write-Host "Module  : $modulePath"
Write-Host "Command : $commandPath"
Write-Host "Config  : $configPath"
Write-Host ""

try {
    $status = Test-AntmuxJulesPublisher -ConfigPath $configPath
    $status | Format-List
}
catch {
    Write-Warning $_.Exception.Message
    Write-Host "The module is installed, but Git must be available before the first publication."
}

Write-Host "Manual dry run:"
Write-Host "& `"$commandPath`" -SummaryPath `"$Root`communication\resumes\LATEST.md`" -ProjectId PROJECT-000000 -DryRun"
