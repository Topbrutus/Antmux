#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$StartupScript = (Join-Path $PSScriptRoot "Start-Antmux.ps1"),
    [string]$ConfigPath,
    [switch]$ValidationOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-AntmuxDriveRoot {
    if (-not [string]::IsNullOrWhiteSpace($env:ANTMUX_ROOT)) {
        return [System.IO.Path]::GetPathRoot([System.IO.Path]::GetFullPath($env:ANTMUX_ROOT))
    }

    return [System.IO.Path]::GetPathRoot([System.IO.Path]::GetFullPath($PSScriptRoot))
}

function Assert-AntmuxDrive {
    param([Parameter(Mandatory = $true)][string]$DriveRoot)

    if ($DriveRoot.TrimEnd([char]92) -ine "D:") {
        throw "ANTMUX_DRIVE_INVALID: expected D:\, received $DriveRoot"
    }

    $drive = New-Object System.IO.DriveInfo($DriveRoot)
    if (-not $drive.IsReady) {
        throw "ANTMUX_DRIVE_NOT_READY: $DriveRoot"
    }
    if ($drive.VolumeLabel -ine "Antmux") {
        throw "ANTMUX_DRIVE_LABEL_INVALID: expected Antmux, received '$($drive.VolumeLabel)'"
    }
}

function Write-AntmuxStartupEvent {
    param(
        [Parameter(Mandatory = $true)][string]$LogPath,
        [Parameter(Mandatory = $true)][string]$Event,
        [Parameter(Mandatory = $true)][string]$Result
    )

    $directory = Split-Path -Parent $LogPath
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $line = "{0} | antmux-core | {1} | {2}" -f (Get-Date).ToString("o"), $Event, $Result
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
}

function Write-AntmuxCoreState {
    param(
        [Parameter(Mandatory = $true)][string]$StatePath,
        [Parameter(Mandatory = $true)][object]$State
    )

    $directory = Split-Path -Parent $StatePath
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $temporaryPath = $StatePath + ".tmp." + [Guid]::NewGuid().ToString("N")
    $json = $State | ConvertTo-Json -Depth 10
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($temporaryPath, $json + [Environment]::NewLine, $encoding)
    Move-Item -LiteralPath $temporaryPath -Destination $StatePath -Force
}

function Get-AntmuxCoreProcesses {
    param([Parameter(Mandatory = $true)][string]$DriveRoot)

    $expectedExecutable = Join-Path $DriveRoot "antmux.exe"
    return @(
        Get-CimInstance Win32_Process -Filter "Name='antmux.exe'" -ErrorAction SilentlyContinue |
            Where-Object {
                ([string]$_.ExecutablePath -ieq $expectedExecutable) -or
                (-not [string]::IsNullOrWhiteSpace([string]$_.CommandLine) -and
                    [string]$_.CommandLine -match [regex]::Escape($expectedExecutable))
            } |
            ForEach-Object {
                [pscustomobject]@{
                    ProcessId = [int]$_.ProcessId
                    ParentProcessId = [int]$_.ParentProcessId
                    ExecutablePath = [string]$_.ExecutablePath
                    CommandLine = [string]$_.CommandLine
                }
            }
    )
}

$driveRoot = Get-AntmuxDriveRoot
Assert-AntmuxDrive -DriveRoot $driveRoot

$startupScriptPath = [System.IO.Path]::GetFullPath($StartupScript)
if (-not (Test-Path -LiteralPath $startupScriptPath -PathType Leaf)) {
    throw "ANTMUX_STARTUP_SCRIPT_NOT_FOUND: $startupScriptPath"
}

$stateDirectory = Join-Path $PSScriptRoot "state"
$coreStatePath = Join-Path $stateDirectory "antmux-core.json"
$corePidPath = Join-Path $stateDirectory "antmux-core.pid"
$startupLogPath = Join-Path $PSScriptRoot "logs\startup.log"
$mutexName = "Global\Antmux-Core"

if ($ValidationOnly) {
    $coreProcesses = @(Get-AntmuxCoreProcesses -DriveRoot $driveRoot)
    [pscustomobject]@{
        Status = "VALIDATION_ONLY"
        DriveRoot = $driveRoot
        StartupScript = $startupScriptPath
        MutexName = $mutexName
        MatchingCoreProcesses = $coreProcesses.Count
        StatePath = $coreStatePath
        PidPath = $corePidPath
    }
    return
}

$mutex = $null
$mutexAcquired = $false
try {
    $mutex = New-Object System.Threading.Mutex($false, $mutexName)
    try {
        $mutexAcquired = $mutex.WaitOne(0, $false)
    }
    catch [System.Threading.AbandonedMutexException] {
        $mutexAcquired = $true
        Write-AntmuxStartupEvent -LogPath $startupLogPath -Event "mutex" -Result "ABANDONED_MUTEX_RECOVERED"
    }

    if (-not $mutexAcquired) {
        Write-AntmuxStartupEvent -LogPath $startupLogPath -Event "start" -Result "SINGLETON_ALREADY_RUNNING mutex=$mutexName"
        Write-Host "ANTMUX STARTUP"
        Write-Host "Core   : SINGLETON_ALREADY_RUNNING"
        return
    }

    $existingCores = @(Get-AntmuxCoreProcesses -DriveRoot $driveRoot)
    if ($existingCores.Count -gt 1) {
        $processIds = ($existingCores | Select-Object -ExpandProperty ProcessId) -join ","
        Write-AntmuxStartupEvent -LogPath $startupLogPath -Event "start" -Result "CORE_AMBIGUOUS pids=$processIds"
        throw "ANTMUX_CORE_AMBIGUOUS: multiple D:\antmux.exe processes were found ($processIds). No process was selected or stopped."
    }

    if ($existingCores.Count -eq 1) {
        $existingCore = $existingCores[0]
        $state = [ordered]@{
            schema_version = 1
            status = "ACTIVE"
            event = "SINGLETON_ALREADY_RUNNING"
            mutex_name = $mutexName
            core_pid = $existingCore.ProcessId
            parent_pid = $existingCore.ParentProcessId
            executable_path = $existingCore.ExecutablePath
            checked_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        }
        Write-AntmuxCoreState -StatePath $coreStatePath -State $state
        [System.IO.File]::WriteAllText($corePidPath, [string]$existingCore.ProcessId, (New-Object System.Text.UTF8Encoding($false)))
        Write-AntmuxStartupEvent -LogPath $startupLogPath -Event "start" -Result "SINGLETON_ALREADY_RUNNING pid=$($existingCore.ProcessId)"
        Write-Host "ANTMUX STARTUP"
        Write-Host ("Core   : SINGLETON_ALREADY_RUNNING PID={0}" -f $existingCore.ProcessId)
        return
    }

    $startingState = [ordered]@{
        schema_version = 1
        status = "STARTING"
        event = "SINGLETON_LOCK_ACQUIRED"
        mutex_name = $mutexName
        launcher_pid = $PID
        startup_script = $startupScriptPath
        started_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    }
    Write-AntmuxCoreState -StatePath $coreStatePath -State $startingState
    [System.IO.File]::WriteAllText($corePidPath, [string]$PID, (New-Object System.Text.UTF8Encoding($false)))
    Write-AntmuxStartupEvent -LogPath $startupLogPath -Event "start" -Result "SINGLETON_LOCK_ACQUIRED launcher_pid=$PID"

    $env:ANTMUX_CORE_SINGLETON = "1"
    if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
        & $startupScriptPath
    }
    else {
        & $startupScriptPath -ConfigPath $ConfigPath
    }

    $exitCode = 0
    if (Test-Path Variable:LASTEXITCODE) {
        $exitCode = [int]$LASTEXITCODE
    }
    $stoppedState = [ordered]@{
        schema_version = 1
        status = "STOPPED"
        event = "STARTUP_SCRIPT_RETURNED"
        mutex_name = $mutexName
        launcher_pid = $PID
        exit_code = $exitCode
        stopped_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    }
    Write-AntmuxCoreState -StatePath $coreStatePath -State $stoppedState
    Write-AntmuxStartupEvent -LogPath $startupLogPath -Event "stop" -Result "STARTUP_SCRIPT_RETURNED exit_code=$exitCode"
}
catch {
    $failedState = [ordered]@{
        schema_version = 1
        status = "FAILED"
        event = "SINGLETON_START_FAILED"
        mutex_name = $mutexName
        launcher_pid = $PID
        error = $_.Exception.Message
        failed_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    }
    Write-AntmuxCoreState -StatePath $coreStatePath -State $failedState
    Write-AntmuxStartupEvent -LogPath $startupLogPath -Event "error" -Result $_.Exception.Message
    throw
}
finally {
    if ($mutexAcquired -and $null -ne $mutex) {
        try {
            $mutex.ReleaseMutex()
        }
        catch {
        }
    }
    if ($null -ne $mutex) {
        $mutex.Dispose()
    }
}
