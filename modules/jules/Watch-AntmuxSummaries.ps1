#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$WatchPath,
    [string]$ProjectId = "PROJECT-000000",
    [switch]$DryRun,
    [switch]$Once,
    [switch]$DisableChatGPTBridge
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-AntmuxRoot {
    if (-not [string]::IsNullOrWhiteSpace($env:ANTMUX_ROOT)) {
        return [System.IO.Path]::GetFullPath($env:ANTMUX_ROOT)
    }

    $modulesDirectory = Split-Path -Parent $PSScriptRoot
    return [System.IO.Path]::GetFullPath((Split-Path -Parent $modulesDirectory))
}

function Assert-AntmuxDrive {
    param([Parameter(Mandatory = $true)][string]$Root)

    $driveRoot = [System.IO.Path]::GetPathRoot($Root)
    $drive = New-Object System.IO.DriveInfo($driveRoot)
    if (-not $drive.IsReady) {
        throw "The Antmux drive is not ready: $driveRoot"
    }
    if ($drive.VolumeLabel -ine "Antmux") {
        throw "The drive must be named Antmux. Current label: '$($drive.VolumeLabel)'."
    }
}

function Resolve-AntmuxPath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Path
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $Root $Path))
}

$root = Get-AntmuxRoot
Assert-AntmuxDrive -Root $root

if ([string]::IsNullOrWhiteSpace($WatchPath)) {
    $WatchPath = Join-Path $root "communication\resumes"
}
else {
    $WatchPath = Resolve-AntmuxPath -Root $root -Path $WatchPath
}

New-Item -ItemType Directory -Force -Path $WatchPath | Out-Null

$publisher = Join-Path $PSScriptRoot "Send-AntmuxSummary.ps1"
if (-not (Test-Path -LiteralPath $publisher -PathType Leaf)) {
    throw "Jules publisher command not found: $publisher"
}

$bridge = Join-Path $root "modules\chatgpt-bridge\Send-AntmuxToChatGPT.ps1"
$bridgeEnabled = (-not $DisableChatGPTBridge) -and (Test-Path -LiteralPath $bridge -PathType Leaf)

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $WatchPath
$watcher.Filter = "*.md"
$watcher.IncludeSubdirectories = $false
$watcher.NotifyFilter = [System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::LastWrite -bor [System.IO.NotifyFilters]::Size
$watcher.EnableRaisingEvents = $true

$changeTypes = [System.IO.WatcherChangeTypes]::Created -bor [System.IO.WatcherChangeTypes]::Renamed
$recent = @{}

Write-Host "JULES SUMMARY WATCHER ACTIVE" -ForegroundColor Green
Write-Host "Folder    : $WatchPath"
Write-Host "Project   : $ProjectId"
Write-Host "Dry run   : $DryRun"
Write-Host "ChatGPT   : $bridgeEnabled"
Write-Host "Stop      : Ctrl+C"
Write-Host ""

try {
    while ($true) {
        $change = $watcher.WaitForChanged($changeTypes, 1000)
        if ($change.TimedOut) {
            continue
        }

        $name = [System.IO.Path]::GetFileName($change.Name)
        if ([string]::IsNullOrWhiteSpace($name)) {
            continue
        }
        if ($name -ieq "LATEST.md") {
            continue
        }
        if ([System.IO.Path]::GetExtension($name) -ine ".md") {
            continue
        }

        $summaryPath = Join-Path $WatchPath $name
        if (-not (Test-Path -LiteralPath $summaryPath -PathType Leaf)) {
            continue
        }

        $now = [datetime]::UtcNow
        if ($recent.ContainsKey($summaryPath)) {
            $elapsed = $now - [datetime]$recent[$summaryPath]
            if ($elapsed.TotalSeconds -lt 5) {
                continue
            }
        }
        $recent[$summaryPath] = $now

        foreach ($key in @($recent.Keys)) {
            if (($now - [datetime]$recent[$key]).TotalMinutes -gt 10) {
                $recent.Remove($key)
            }
        }

        try {
            $parameters = @{
                SummaryPath = $summaryPath
                ProjectId = $ProjectId
            }
            if ($DryRun) {
                $parameters.DryRun = $true
            }

            Write-Host "Detected  : $name" -ForegroundColor Cyan
            & $publisher @parameters

            if ($bridgeEnabled -and (-not $DryRun)) {
                Write-Host "ChatGPT   : handoff to screen 3" -ForegroundColor Magenta
                & $bridge -SummaryPath $summaryPath
            }
            elseif ((-not $DisableChatGPTBridge) -and (-not $bridgeEnabled)) {
                Write-Warning "ChatGPT bridge is not installed; GitHub publication completed without ChatGPT handoff."
            }

            Write-Host ""
            if ($Once) {
                break
            }
        }
        catch {
            Write-Warning ("Jules pipeline could not process '{0}': {1}" -f $name, $_.Exception.Message)
            Write-Host ""
            if ($Once) {
                throw
            }
        }
    }
}
finally {
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
}
