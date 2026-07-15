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

$publisher = Join-Path $Root "modules\jules\Send-AntmuxSummary.ps1"
if (-not (Test-Path -LiteralPath $publisher -PathType Leaf)) {
    throw "Install Jules Summary Publisher first. Missing: $publisher"
}

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
}
catch {
}

$baseUrl = "https://raw.githubusercontent.com/Topbrutus/Antmux/main"
$moduleDirectory = Join-Path $Root "modules\jules"
$watcherPath = Join-Path $moduleDirectory "Watch-AntmuxSummaries.ps1"
$launcherPath = Join-Path $Root "jules-watch.cmd"
$temporary = "$watcherPath.download"

New-Item -ItemType Directory -Force -Path $moduleDirectory | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root "communication\resumes") | Out-Null

Invoke-WebRequest -UseBasicParsing `
    -Uri "$baseUrl/modules/jules/Watch-AntmuxSummaries.ps1" `
    -OutFile $temporary
Move-Item -LiteralPath $temporary -Destination $watcherPath -Force

$tokens = $null
$errors = $null
$null = [System.Management.Automation.Language.Parser]::ParseFile(
    $watcherPath,
    [ref]$tokens,
    [ref]$errors
)
if ($errors.Count -gt 0) {
    throw "PowerShell syntax error in $watcherPath : $($errors[0].Message)"
}

$launcher = @'
@echo off
set "ANTMUX_ROOT=%~d0\"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~d0\modules\jules\Watch-AntmuxSummaries.ps1"
'@

[System.IO.File]::WriteAllText(
    $launcherPath,
    $launcher,
    (New-Object System.Text.ASCIIEncoding)
)

Write-Host ""
Write-Host "JULES SUMMARY WATCHER INSTALLED" -ForegroundColor Green
Write-Host "Watcher : $watcherPath"
Write-Host "Launcher: $launcherPath"
Write-Host "Folder  : $(Join-Path $Root 'communication\resumes')"
Write-Host ""
Write-Host "Start Jules with:"
Write-Host "& `"$launcherPath`""
