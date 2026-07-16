#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$ConfigPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Get-AntmuxHome {
    if (-not [string]::IsNullOrWhiteSpace($env:ANTMUX_HOME)) {
        return [System.IO.Path]::GetFullPath($env:ANTMUX_HOME)
    }

    return [System.IO.Path]::GetFullPath($PSScriptRoot)
}

function Get-AntmuxDriveRoot {
    param([Parameter(Mandatory = $true)][string]$StartupHome)

    if (-not [string]::IsNullOrWhiteSpace($env:ANTMUX_ROOT)) {
        return [System.IO.Path]::GetFullPath($env:ANTMUX_ROOT)
    }

    return [System.IO.Path]::GetPathRoot($StartupHome)
}

function Assert-AntmuxDrive {
    param([Parameter(Mandatory = $true)][string]$DriveRoot)

    $driveRoot = [System.IO.Path]::GetPathRoot($DriveRoot)
    if ($driveRoot.TrimEnd([char]92) -ne "D:") {
        throw "Antmux must use D:\. Current root: $DriveRoot"
    }

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

function Ensure-AntmuxDirectory {
    param([Parameter(Mandatory = $true)][string]$Path)

    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Get-AntmuxConfig {
    param(
        [Parameter(Mandatory = $true)][string]$StartupHome,
        [string]$Path
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        $Path = Join-Path $StartupHome "config\services.json"
    }

    $resolved = Resolve-AntmuxPath -Root $StartupHome -Path $Path
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        throw "Services config not found: $resolved"
    }

    $config = Get-Content -LiteralPath $resolved -Raw | ConvertFrom-Json
    if ($null -eq $config.services) {
        throw "Services config must contain a services array: $resolved"
    }

    foreach ($service in @($config.services)) {
        foreach ($required in @("id", "enabled", "type", "launcher", "match", "window", "required")) {
            if ($null -eq $service.PSObject.Properties[$required]) {
                throw "Missing service property '$required' in $resolved"
            }
        }
    }

    return [pscustomobject]@{
        Path = $resolved
        Data = $config
    }
}

function Test-TextMatch {
    param(
        [string]$Text,
        [string]$Needle
    )

    if ([string]::IsNullOrWhiteSpace($Text) -or [string]::IsNullOrWhiteSpace($Needle)) {
        return $false
    }

    return $Text -match [regex]::Escape($Needle)
}

function Get-ProcessSnapshot {
    param([Parameter(Mandatory = $true)][int]$ProcessId)

    $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $cim) {
        return $null
    }

    $startTime = $null
    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -ne $process) {
        try {
            $startTime = $process.StartTime
        }
        catch {
        }
    }

    return [pscustomobject]@{
        ProcessId = [int]$cim.ProcessId
        Name = [string]$cim.Name
        ExecutablePath = [string]$cim.ExecutablePath
        CommandLine = [string]$cim.CommandLine
        ParentProcessId = [int]$cim.ParentProcessId
        StartTime = $startTime
    }
}

function Test-AntmuxProcessMatchesService {
    param(
        [Parameter(Mandatory = $true)][object]$Process,
        [Parameter(Mandatory = $true)][object]$Service,
        [Parameter(Mandatory = $true)][string]$Root
    )

    $launcher = Resolve-AntmuxPath -Root $Root -Path ([string]$Service.launcher)
    $match = [string]$Service.match
    $launcherName = [System.IO.Path]::GetFileName($launcher)

    foreach ($needle in @($match, $launcher, $launcherName)) {
        if (Test-TextMatch -Text ([string]$Process.CommandLine) -Needle $needle) {
            return $true
        }

        if (Test-TextMatch -Text ([string]$Process.ExecutablePath) -Needle $needle) {
            return $true
        }
    }

    return $false
}

function Find-AntmuxServiceProcess {
    param(
        [Parameter(Mandatory = $true)][string]$DriveRoot,
        [Parameter(Mandatory = $true)][object]$Service,
        [int]$PreferredPid = 0
    )

    if ($PreferredPid -gt 0) {
        $preferred = Get-ProcessSnapshot -ProcessId $PreferredPid
        if ($null -ne $preferred -and (Test-AntmuxProcessMatchesService -Process $preferred -Service $Service -Root $DriveRoot)) {
            return $preferred
        }
    }

    $matches = foreach ($item in Get-CimInstance Win32_Process) {
        $snapshot = [pscustomobject]@{
            ProcessId = [int]$item.ProcessId
            Name = [string]$item.Name
            ExecutablePath = [string]$item.ExecutablePath
            CommandLine = [string]$item.CommandLine
            ParentProcessId = [int]$item.ParentProcessId
            StartTime = $null
        }

        if (Test-AntmuxProcessMatchesService -Process $snapshot -Service $Service -Root $DriveRoot) {
            $snapshot
        }
    }

    if ($null -eq $matches) {
        return $null
    }

    return $matches | Sort-Object ProcessId -Descending | Select-Object -First 1
}

function Get-AntmuxLogPath {
    param(
        [Parameter(Mandatory = $true)][string]$StartupHome,
        [Parameter(Mandatory = $true)][string]$ServiceId
    )

    return Join-Path $StartupHome ("logs\" + $ServiceId + ".log")
}

function Get-AntmuxStatePath {
    param(
        [Parameter(Mandatory = $true)][string]$StartupHome,
        [Parameter(Mandatory = $true)][string]$ServiceId
    )

    return Join-Path $StartupHome ("state\" + $ServiceId + ".json")
}

function Get-AntmuxPidPath {
    param(
        [Parameter(Mandatory = $true)][string]$StartupHome,
        [Parameter(Mandatory = $true)][string]$ServiceId
    )

    return Join-Path $StartupHome ("state\" + $ServiceId + ".pid")
}

function Invoke-AntmuxLogRotation {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return
    }

    $item = Get-Item -LiteralPath $Path
    if ($item.Length -lt 1048576) {
        return
    }

    $backup = "$Path.1"
    if (Test-Path -LiteralPath $backup -PathType Leaf) {
        Remove-Item -LiteralPath $backup -Force
    }

    Move-Item -LiteralPath $Path -Destination $backup -Force
}

function Write-AntmuxLogLine {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ServiceId,
        [Parameter(Mandatory = $true)][string]$Action,
        [Parameter(Mandatory = $true)][string]$Result
    )

    $directory = Split-Path -Parent $Path
    Ensure-AntmuxDirectory -Path $directory
    Invoke-AntmuxLogRotation -Path $Path

    $line = "{0} | {1} | {2} | {3}" -f (Get-Date).ToString("o"), $ServiceId, $Action, $Result
    Add-Content -LiteralPath $Path -Value $line -Encoding UTF8
}

function Write-AntmuxState {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][object]$State
    )

    $directory = Split-Path -Parent $Path
    Ensure-AntmuxDirectory -Path $directory

    $json = $State | ConvertTo-Json -Depth 8
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $json, $encoding)
}

function Remove-AntmuxStateFiles {
    param(
        [Parameter(Mandatory = $true)][string]$StatePath,
        [Parameter(Mandatory = $true)][string]$PidPath
    )

    foreach ($path in @($StatePath, $PidPath)) {
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Force
        }
    }
}

function Read-AntmuxState {
    param([Parameter(Mandatory = $true)][string]$StatePath)

    if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) {
        return $null
    }

    return Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
}

function Get-AntmuxServiceDisplayName {
    param([Parameter(Mandatory = $true)][object]$Service)

    if (-not [string]::IsNullOrWhiteSpace([string]$Service.name)) {
        return [string]$Service.name
    }

    return [string]$Service.id
}

function Start-AntmuxService {
    param(
        [Parameter(Mandatory = $true)][string]$StartupHome,
        [Parameter(Mandatory = $true)][string]$DriveRoot,
        [Parameter(Mandatory = $true)][object]$Service,
        [Parameter(Mandatory = $true)][bool]$ValidationMode,
        [Parameter(Mandatory = $true)][string]$StartupLogPath,
        [Parameter(Mandatory = $true)][string]$ErrorLogPath
    )

    $serviceId = [string]$Service.id
    $displayName = Get-AntmuxServiceDisplayName -Service $Service
    $logPath = Get-AntmuxLogPath -StartupHome $StartupHome -ServiceId $serviceId
    $statePath = Get-AntmuxStatePath -StartupHome $StartupHome -ServiceId $serviceId
    $pidPath = Get-AntmuxPidPath -StartupHome $StartupHome -ServiceId $serviceId
    $existingPid = 0
    if (Test-Path -LiteralPath $pidPath -PathType Leaf) {
        try {
            $existingPid = [int](Get-Content -LiteralPath $pidPath -Raw).Trim()
        }
        catch {
            $existingPid = 0
        }
    }

    $state = Read-AntmuxState -StatePath $statePath
    $existing = Find-AntmuxServiceProcess -DriveRoot $DriveRoot -Service $Service -PreferredPid $existingPid

    if ($null -ne $existing) {
        $activeState = [pscustomobject]@{
            id = $serviceId
            name = $displayName
            status = "ACTIVE"
            pid = $existing.ProcessId
            started_at = if ($null -ne $existing.StartTime) { $existing.StartTime.ToString("o") } else { (Get-Date).ToString("o") }
            launcher = Resolve-AntmuxPath -Root $DriveRoot -Path ([string]$Service.launcher)
            command_line = [string]$existing.CommandLine
            log_path = $logPath
            error = $null
            checked_at = (Get-Date).ToString("o")
        }

        Write-AntmuxState -Path $statePath -State $activeState
        [System.IO.File]::WriteAllText($pidPath, [string]$existing.ProcessId, (New-Object System.Text.UTF8Encoding($false)))
        Write-AntmuxLogLine -Path $StartupLogPath -ServiceId $serviceId -Action "start" -Result "already-active pid=$($existing.ProcessId)"
        return [pscustomobject]@{
            Name = $displayName
            State = "ACTIVE"
            PID = $existing.ProcessId
            Started = $activeState.started_at
            Log = $logPath
            Error = $null
            AlreadyActive = $true
        }
    }

    Remove-AntmuxStateFiles -StatePath $statePath -PidPath $pidPath

    $launcherPath = Resolve-AntmuxPath -Root $DriveRoot -Path ([string]$Service.launcher)
    $scriptPath = Join-Path $DriveRoot "modules\jules\Watch-AntmuxSummaries.ps1"
    $processFile = $launcherPath
    $arguments = @()
    $workingDirectory = $DriveRoot

    if ($ValidationMode) {
        $processFile = "powershell.exe"
        $arguments = @(
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            $scriptPath,
            "-DisableChatGPTBridge"
        )
    }

    Ensure-AntmuxDirectory -Path (Split-Path -Parent $logPath)

    $startProcessParams = @{
        FilePath = $processFile
        WorkingDirectory = $workingDirectory
        WindowStyle = "Hidden"
        PassThru = $true
        RedirectStandardOutput = $logPath
        RedirectStandardError = $ErrorLogPath
    }

    $cleanArguments = @(
        $arguments | Where-Object {
            $null -ne $_ -and
            -not [string]::IsNullOrWhiteSpace([string]$_)
        }
    )

    if ($cleanArguments.Count -gt 0) {
        $startProcessParams.ArgumentList = $cleanArguments
    }

    $started = Start-Process @startProcessParams

    $resolved = $null
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        Start-Sleep -Milliseconds 250
        $resolved = Find-AntmuxServiceProcess -DriveRoot $DriveRoot -Service $Service -PreferredPid $started.Id
        if ($null -ne $resolved) {
            break
        }
    }

    if ($null -eq $resolved) {
        try {
            Stop-Process -Id $started.Id -Force -ErrorAction SilentlyContinue
        }
        catch {
        }

        Write-AntmuxLogLine -Path $StartupLogPath -ServiceId $serviceId -Action "start" -Result "failed-to-confirm-process"
        Write-AntmuxLogLine -Path $ErrorLogPath -ServiceId $serviceId -Action "start" -Result "failed-to-confirm-process"
        throw "The service did not become active in time: $displayName"
    }

    $startedAt = if ($null -ne $resolved.StartTime) { $resolved.StartTime.ToString("o") } else { (Get-Date).ToString("o") }
    $record = [pscustomobject]@{
        id = $serviceId
        name = $displayName
        status = "ACTIVE"
        pid = $resolved.ProcessId
        started_at = $startedAt
        launcher = $launcherPath
        command_line = [string]$resolved.CommandLine
        log_path = $logPath
        error = $null
        checked_at = (Get-Date).ToString("o")
    }

    Write-AntmuxState -Path $statePath -State $record
    [System.IO.File]::WriteAllText($pidPath, [string]$resolved.ProcessId, (New-Object System.Text.UTF8Encoding($false)))

    Write-AntmuxLogLine -Path $StartupLogPath -ServiceId $serviceId -Action "start" -Result "active pid=$($resolved.ProcessId)"

    return [pscustomobject]@{
        Name = $displayName
        State = "ACTIVE"
        PID = $resolved.ProcessId
        Started = $startedAt
        Log = $logPath
        Error = $null
        AlreadyActive = $false
    }
}

$antmuxHome = Get-AntmuxHome
$driveRoot = Get-AntmuxDriveRoot -StartupHome $antmuxHome
Assert-AntmuxDrive -DriveRoot $driveRoot
$env:ANTMUX_HOME = $antmuxHome
$env:ANTMUX_ROOT = $driveRoot

Ensure-AntmuxDirectory -Path (Join-Path $antmuxHome "logs")
Ensure-AntmuxDirectory -Path (Join-Path $antmuxHome "state")

$configRecord = Get-AntmuxConfig -StartupHome $antmuxHome -Path $ConfigPath
$services = @($configRecord.Data.services)

$startupLogPath = Join-Path $antmuxHome "logs\startup.log"
$errorLogPath = Join-Path $antmuxHome "logs\errors.log"
$validationMode = ($env:ANTMUX_VALIDATION -eq "1") -or ($env:ANTMUX_NO_CLI -eq "1") -or ($env:ANTMUX_NO_BRIDGE -eq "1")

$results = @()
foreach ($service in $services) {
    if (-not [bool]$service.enabled) {
        continue
    }

    if ([string]$service.type -ine "process") {
        continue
    }

    $result = Start-AntmuxService -StartupHome $antmuxHome -DriveRoot $driveRoot -Service $service -ValidationMode $validationMode -StartupLogPath $startupLogPath -ErrorLogPath $errorLogPath
    $results += $result
}

Write-Host "ANTMUX STARTUP"
Write-Host ("Drive  : {0} [Antmux]" -f $driveRoot)

foreach ($result in $results) {
    if ($result.AlreadyActive) {
        Write-Host ("{0}  : ALREADY ACTIVE PID={1}" -f $result.Name, $result.PID)
    }
    else {
        Write-Host ("{0}  : ACTIVE PID={1}" -f $result.Name, $result.PID)
    }
}

if ($validationMode) {
    Write-Host "Bridge : VALIDATION MODE"
    Write-Host "CLI    : SKIPPED"
}
else {
    Write-Host "Bridge : READY - invoked by Jules when needed"
    Write-Host "CLI    : STARTING"
    $cliPath = Join-Path $driveRoot "antmux.exe"
    if (-not (Test-Path -LiteralPath $cliPath -PathType Leaf)) {
        throw "Antmux CLI not found: $cliPath"
    }

    & $cliPath
}
