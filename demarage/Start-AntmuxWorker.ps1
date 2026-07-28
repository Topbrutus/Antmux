#requires -Version 5.1

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")]
    [string]$InstanceId,

    [string]$DisplayName,
    [string]$AccountAlias = "",
    [string]$Role = "worker",

    [Parameter(Mandatory = $true)]
    [string]$Workspace,

    [string]$CommandPath,
    [string[]]$CommandArguments = @(),
    [switch]$Launch
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

function Write-AntmuxWorkerProfile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][object]$Profile
    )

    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $directory | Out-Null

    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        $backupPath = $Path + ".backup." + (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssfffZ") + ".json"
        Copy-Item -LiteralPath $Path -Destination $backupPath
    }

    $temporaryPath = $Path + ".tmp." + [Guid]::NewGuid().ToString("N")
    $json = $Profile | ConvertTo-Json -Depth 12
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($temporaryPath, $json + [Environment]::NewLine, $encoding)
    Move-Item -LiteralPath $temporaryPath -Destination $Path -Force
}

$driveRoot = Get-AntmuxDriveRoot
Assert-AntmuxDrive -DriveRoot $driveRoot

$resolvedWorkspace = [System.IO.Path]::GetFullPath($Workspace)
if (-not (Test-Path -LiteralPath $resolvedWorkspace -PathType Container)) {
    throw "WORKER_WORKSPACE_NOT_FOUND: $resolvedWorkspace"
}

if ([string]::IsNullOrWhiteSpace($DisplayName)) {
    $DisplayName = $InstanceId
}
if ([string]::IsNullOrWhiteSpace($Role)) {
    throw "WORKER_ROLE_INVALID: Role must not be empty"
}

$coreProcesses = @(Get-AntmuxCoreProcesses -DriveRoot $driveRoot)
if ($coreProcesses.Count -eq 0) {
    throw "ANTMUX_CORE_NOT_RUNNING: no verified D:\antmux.exe process was found"
}
if ($coreProcesses.Count -gt 1) {
    $processIds = ($coreProcesses | Select-Object -ExpandProperty ProcessId) -join ","
    throw "ANTMUX_CORE_AMBIGUOUS: multiple verified core processes were found ($processIds). No process was selected or stopped."
}
$core = $coreProcesses[0]

$resolvedCommandPath = $null
if (-not [string]::IsNullOrWhiteSpace($CommandPath)) {
    if ([System.IO.Path]::IsPathRooted($CommandPath)) {
        $resolvedCommandPath = [System.IO.Path]::GetFullPath($CommandPath)
    }
    else {
        $resolvedCommandPath = [System.IO.Path]::GetFullPath((Join-Path $resolvedWorkspace $CommandPath))
    }
}

if ($Launch) {
    if ([string]::IsNullOrWhiteSpace($resolvedCommandPath)) {
        throw "WORKER_COMMAND_REQUIRED: -CommandPath is required with -Launch"
    }
    if (-not (Test-Path -LiteralPath $resolvedCommandPath -PathType Leaf)) {
        throw "WORKER_COMMAND_NOT_FOUND: $resolvedCommandPath"
    }
}

$env:ANTMUX_INSTANCE_ID = $InstanceId
$env:ANTMUX_DISPLAY_NAME = $DisplayName
$env:ANTMUX_ACCOUNT_ALIAS = $AccountAlias
$env:ANTMUX_ROLE = $Role
$env:ANTMUX_WORKSPACE = $resolvedWorkspace
$env:ANTMUX_WORKER_ONLY = "1"
$env:ANTMUX_NO_CLI = "1"
$env:ANTMUX_NO_BRIDGE = "1"

$profileDirectory = Join-Path $PSScriptRoot "state\workers"
$profilePath = Join-Path $profileDirectory ($InstanceId + ".json")
$profile = [ordered]@{
    schema_version = 1
    instance_id = $InstanceId
    display_name = $DisplayName
    account_alias = $AccountAlias
    role = $Role
    workspace = $resolvedWorkspace
    worker_only = $true
    no_cli = $true
    no_bridge = $true
    core_pid = $core.ProcessId
    core_parent_pid = $core.ParentProcessId
    command_path = $resolvedCommandPath
    command_arguments = @($CommandArguments)
    launch_requested = [bool]$Launch
    status = if ($Launch) { "READY_TO_LAUNCH" } else { "PREPARED" }
    prepared_at_utc = (Get-Date).ToUniversalTime().ToString("o")
}
Write-AntmuxWorkerProfile -Path $profilePath -Profile $profile

if (-not $Launch) {
    [pscustomobject]@{
        Status = "WORKER_PROFILE_PREPARED"
        InstanceId = $InstanceId
        CorePid = $core.ProcessId
        Workspace = $resolvedWorkspace
        ProfilePath = $profilePath
        LaunchPerformed = $false
    }
    return
}

$startParameters = @{
    FilePath = $resolvedCommandPath
    WorkingDirectory = $resolvedWorkspace
    PassThru = $true
}
$cleanArguments = @(
    $CommandArguments | Where-Object {
        $null -ne $_ -and -not [string]::IsNullOrWhiteSpace([string]$_)
    }
)
if ($cleanArguments.Count -gt 0) {
    $startParameters.ArgumentList = $cleanArguments
}

$workerProcess = Start-Process @startParameters
$launchedProfile = [ordered]@{
    schema_version = 1
    instance_id = $InstanceId
    display_name = $DisplayName
    account_alias = $AccountAlias
    role = $Role
    workspace = $resolvedWorkspace
    worker_only = $true
    no_cli = $true
    no_bridge = $true
    core_pid = $core.ProcessId
    worker_pid = $workerProcess.Id
    command_path = $resolvedCommandPath
    command_arguments = @($cleanArguments)
    launch_requested = $true
    status = "LAUNCHED"
    launched_at_utc = (Get-Date).ToUniversalTime().ToString("o")
}
Write-AntmuxWorkerProfile -Path $profilePath -Profile $launchedProfile

[pscustomobject]@{
    Status = "WORKER_LAUNCHED"
    InstanceId = $InstanceId
    CorePid = $core.ProcessId
    WorkerPid = $workerProcess.Id
    Workspace = $resolvedWorkspace
    ProfilePath = $profilePath
    LaunchPerformed = $true
}
