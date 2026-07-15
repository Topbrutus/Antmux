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
}

$baseUrl = "https://raw.githubusercontent.com/Topbrutus/Antmux/main"
$bridgeDirectory = Join-Path $Root "modules\chatgpt-bridge"
$julesDirectory = Join-Path $Root "modules\jules"
$configDirectory = Join-Path $Root "config"
$stateDirectory = Join-Path $Root "communication\chatgpt-bridge"
$backupStamp = Get-Date -Format "yyyyMMdd-HHmmss"

New-Item -ItemType Directory -Force -Path $bridgeDirectory | Out-Null
New-Item -ItemType Directory -Force -Path $julesDirectory | Out-Null
New-Item -ItemType Directory -Force -Path $configDirectory | Out-Null
New-Item -ItemType Directory -Force -Path $stateDirectory | Out-Null

$downloads = @(
    [pscustomobject]@{
        Url = "$baseUrl/modules/chatgpt-bridge/ChatGPT.Bridge.psm1"
        Path = (Join-Path $bridgeDirectory "ChatGPT.Bridge.psm1")
    },
    [pscustomobject]@{
        Url = "$baseUrl/modules/chatgpt-bridge/Send-AntmuxToChatGPT.ps1"
        Path = (Join-Path $bridgeDirectory "Send-AntmuxToChatGPT.ps1")
    },
    [pscustomobject]@{
        Url = "$baseUrl/config/chatgpt-bridge.json"
        Path = (Join-Path $configDirectory "chatgpt-bridge.json")
    },
    [pscustomobject]@{
        Url = "$baseUrl/modules/jules/Watch-AntmuxSummaries.ps1"
        Path = (Join-Path $julesDirectory "Watch-AntmuxSummaries.ps1")
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

$configPath = Join-Path $configDirectory "chatgpt-bridge.json"
$null = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json

foreach ($scriptPath in @(
    (Join-Path $bridgeDirectory "ChatGPT.Bridge.psm1"),
    (Join-Path $bridgeDirectory "Send-AntmuxToChatGPT.ps1"),
    (Join-Path $julesDirectory "Watch-AntmuxSummaries.ps1")
)) {
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

$modulePath = Join-Path $bridgeDirectory "ChatGPT.Bridge.psm1"
Import-Module -Name $modulePath -Force

Write-Host ""
Write-Host "CHATGPT SCREEN 3 BRIDGE INSTALLED" -ForegroundColor Green
Write-Host "Root    : $Root"
Write-Host "Module  : $modulePath"
Write-Host "Command : $(Join-Path $bridgeDirectory 'Send-AntmuxToChatGPT.ps1')"
Write-Host "Config  : $configPath"
Write-Host "Jules   : $(Join-Path $julesDirectory 'Watch-AntmuxSummaries.ps1')"
Write-Host ""

try {
    Test-ChatGPTBridgeTarget -ConfigPath $configPath | Format-List
}
catch {
    Write-Warning $_.Exception.Message
}

Write-Host "Safe target test:"
Write-Host "& `"$(Join-Path $bridgeDirectory 'Send-AntmuxToChatGPT.ps1')`" -SummaryPath `"$(Join-Path $Root 'communication\resumes\JOB-000001-TEST.md')`" -TestOnly"
Write-Host ""
Write-Host "Restart Jules after installation so the updated watcher loads the bridge."
