#requires -Version 5.1

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$repoRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
$modulePath = Join-Path $repoRoot "modules\chatgpt-bridge\ChatGPT.BridgeTarget.psm1"
$singletonPath = Join-Path $repoRoot "demarage\Start-AntmuxSingleton.ps1"
$workerPath = Join-Path $repoRoot "demarage\Start-AntmuxWorker.ps1"
$exampleConfigPath = Join-Path $repoRoot "config\chatgpt-bridge-target.example.json"

$script:Total = 0
$script:Passed = 0
$script:Failed = 0

function Invoke-RecoveryCheck {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Test
    )

    $script:Total++
    try {
        $result = & $Test
        if ($result) {
            $script:Passed++
            Write-Host "[PASS] $Name"
        }
        else {
            $script:Failed++
            Write-Host "[FAIL] $Name"
        }
    }
    catch {
        $script:Failed++
        Write-Host "[FAIL] $Name - $($_.Exception.Message)"
    }
}

function Test-PowerShellParse {
    param([Parameter(Mandatory = $true)][string]$Path)

    $tokens = $null
    $parseErrors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$parseErrors)
    return @($parseErrors).Count -eq 0
}

Invoke-RecoveryCheck "canonical target example exists" { Test-Path -LiteralPath $exampleConfigPath -PathType Leaf }
Invoke-RecoveryCheck "bridge target module exists" { Test-Path -LiteralPath $modulePath -PathType Leaf }
Invoke-RecoveryCheck "singleton wrapper exists" { Test-Path -LiteralPath $singletonPath -PathType Leaf }
Invoke-RecoveryCheck "worker launcher exists" { Test-Path -LiteralPath $workerPath -PathType Leaf }

Invoke-RecoveryCheck "bridge module parses on PowerShell 5.1" { Test-PowerShellParse -Path $modulePath }
Invoke-RecoveryCheck "singleton wrapper parses on PowerShell 5.1" { Test-PowerShellParse -Path $singletonPath }
Invoke-RecoveryCheck "worker launcher parses on PowerShell 5.1" { Test-PowerShellParse -Path $workerPath }

Invoke-RecoveryCheck "example config is valid JSON" {
    $config = Get-Content -LiteralPath $exampleConfigPath -Raw | ConvertFrom-Json
    [int]$config.schema_version -eq 1 -and
        [bool]$config.enabled -and
        [string]$config.target_type -eq "nino-tile" -and
        [int]$config.tile_number -eq 1
}

$moduleText = Get-Content -LiteralPath $modulePath -Raw
$singletonText = Get-Content -LiteralPath $singletonPath -Raw
$workerText = Get-Content -LiteralPath $workerPath -Raw

Invoke-RecoveryCheck "bridge exports canonical target functions" {
    @(
        "Get-ChatGPTBridgeTarget",
        "Test-ChatGPTBridgeTarget",
        "Set-ChatGPTBridgeTarget",
        "Clear-ChatGPTBridgeTarget"
    ) | ForEach-Object { $moduleText.Contains($_) } | Where-Object { -not $_ } | Measure-Object | Select-Object -ExpandProperty Count | ForEach-Object { $_ -eq 0 }
}
Invoke-RecoveryCheck "bridge adapter contains no send-key automation" { $moduleText -notmatch "SendKeys|SEND_ACTION_EXECUTED" }
Invoke-RecoveryCheck "bridge adapter contains no network request" { $moduleText -notmatch "Invoke-WebRequest|Invoke-RestMethod|System\.Net\.Http" }
Invoke-RecoveryCheck "bridge adapter does not launch processes" { $moduleText -notmatch "Start-Process|System\.Diagnostics\.Process" }
Invoke-RecoveryCheck "singleton uses the required global mutex" { $singletonText.Contains("Global\Antmux-Core") }
Invoke-RecoveryCheck "singleton refuses ambiguous cores" { $singletonText.Contains("ANTMUX_CORE_AMBIGUOUS") }
Invoke-RecoveryCheck "singleton never kills a process" { $singletonText -notmatch "Stop-Process|taskkill|Terminate\(" }
Invoke-RecoveryCheck "worker is inert without explicit Launch" { $workerText.Contains("if (-not `$Launch)") -and $workerText.Contains("LaunchPerformed = `$false") }
Invoke-RecoveryCheck "worker disables CLI and bridge" { $workerText.Contains("ANTMUX_NO_CLI") -and $workerText.Contains("ANTMUX_NO_BRIDGE") }
Invoke-RecoveryCheck "worker refuses ambiguous cores" { $workerText.Contains("ANTMUX_CORE_AMBIGUOUS") }
Invoke-RecoveryCheck "worker never kills a process" { $workerText -notmatch "Stop-Process|taskkill|Terminate\(" }

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("antmux-recovery-validator-" + [Guid]::NewGuid().ToString("N"))
$previousRoot = $env:ANTMUX_ROOT
try {
    New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
    $env:ANTMUX_ROOT = $tempRoot
    $configPath = Join-Path $tempRoot "config\chatgpt-bridge-target.json"
    $sessionPath = Join-Path $tempRoot "tools\ninoscreens\data\dashboard_session.json"
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $sessionPath) | Out-Null

    Import-Module $modulePath -Force -Prefix Recovery

    $written = Set-RecoveryChatGPTBridgeTarget -ConfigPath $configPath -TileNumber 1 -SelectedBy "Brutus"
    Invoke-RecoveryCheck "Set target writes canonical configuration" {
        $written.Status -eq "TARGET_CONFIGURATION_WRITTEN" -and (Test-Path -LiteralPath $configPath -PathType Leaf)
    }

    $validSession = [ordered]@{
        tiles = @(
            [ordered]@{
                TileNumber = 1
                Url = "https://chatgpt.com/c/recovery-test"
                Visible = $true
                Loaded = $true
                PromptFound = $true
                DynamicScreen = "\\.\DISPLAY4"
            },
            [ordered]@{
                TileNumber = 13
                Url = "https://chatgpt.com/c/other-test"
                Visible = $true
                Loaded = $true
                PromptFound = $true
                DynamicScreen = "\\.\DISPLAY5"
            }
        )
    }
    $validSession | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $sessionPath -Encoding UTF8

    $target = Get-RecoveryChatGPTBridgeTarget -ConfigPath $configPath -NinoSessionPath $sessionPath
    Invoke-RecoveryCheck "configured tile resolves deterministically" {
        $target.Status -eq "TARGET_RESOLVED_BY_CONFIGURATION" -and $target.Valid -and $target.TileNumber -eq 1
    }
    Invoke-RecoveryCheck "other ChatGPT tiles are reported, not selected" {
        @($target.OtherChatGPTTiles).Count -eq 1 -and @($target.OtherChatGPTTiles)[0] -eq 13
    }
    Invoke-RecoveryCheck "target exposes evidence fields" {
        $target.TileUrl -eq "https://chatgpt.com/c/recovery-test" -and
            $target.Visible -eq $true -and
            $target.Loaded -eq $true -and
            $target.PromptFound -eq $true
    }

    $invalidUrlSession = [ordered]@{
        tiles = @(
            [ordered]@{
                TileNumber = 1
                Url = "https://example.invalid/"
                Visible = $true
                Loaded = $true
                PromptFound = $true
            }
        )
    }
    $invalidUrlSession | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $sessionPath -Encoding UTF8
    $invalidUrlTarget = Test-RecoveryChatGPTBridgeTarget -ConfigPath $configPath -NinoSessionPath $sessionPath
    Invoke-RecoveryCheck "disallowed target URL is rejected" {
        $invalidUrlTarget.Status -eq "TARGET_URL_NOT_ALLOWED" -and -not $invalidUrlTarget.Valid
    }

    $invisibleSession = [ordered]@{
        tiles = @(
            [ordered]@{
                TileNumber = 1
                Url = "https://chatgpt.com/c/recovery-test"
                Visible = $false
                Loaded = $true
                PromptFound = $true
            }
        )
    }
    $invisibleSession | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $sessionPath -Encoding UTF8
    $invisibleTarget = Test-RecoveryChatGPTBridgeTarget -ConfigPath $configPath -NinoSessionPath $sessionPath
    Invoke-RecoveryCheck "invisible configured tile is rejected" {
        $invisibleTarget.Status -eq "TARGET_NOT_VISIBLE" -and -not $invisibleTarget.Valid
    }

    $cleared = Clear-RecoveryChatGPTBridgeTarget -ConfigPath $configPath
    Invoke-RecoveryCheck "Clear target archives instead of deleting silently" {
        $cleared.Status -eq "TARGET_CONFIGURATION_CLEARED" -and
            -not (Test-Path -LiteralPath $configPath) -and
            (Test-Path -LiteralPath $cleared.ArchivePath -PathType Leaf)
    }
}
finally {
    $env:ANTMUX_ROOT = $previousRoot
    Remove-Module ChatGPT.BridgeTarget -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host ("TOTAL: {0}" -f $script:Total)
Write-Host ("PASSED: {0}" -f $script:Passed)
Write-Host ("FAILED: {0}" -f $script:Failed)
if ($script:Failed -eq 0) {
    Write-Host "ALL_TESTS: PASS"
    exit 0
}

Write-Host "ALL_TESTS: FAIL"
exit 1
