#requires -Version 5.1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-HookResult {
    param([string]$SystemMessage)

    $result = [ordered]@{ continue = $true }
    if (-not [string]::IsNullOrWhiteSpace($SystemMessage)) {
        $result.systemMessage = $SystemMessage
    }

    [Console]::Out.WriteLine(($result | ConvertTo-Json -Compress))
    exit 0
}

function Get-SafeToken {
    param(
        [object]$Value,
        [string]$Fallback
    )

    $token = [string]$Value
    if ([string]::IsNullOrWhiteSpace($token)) {
        $token = $Fallback
    }

    $token = [regex]::Replace($token, "[^A-Za-z0-9_-]", "_")
    if ($token.Length -gt 32) {
        $token = $token.Substring(0, 32)
    }

    return $token
}

function Write-Utf8NoBom {
    param(
        [string]$Path,
        [string]$Content
    )

    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

$root = if ([string]::IsNullOrWhiteSpace($env:ANTMUX_ROOT)) { "D:\" } else { $env:ANTMUX_ROOT }
$summaryDirectory = Join-Path $root "communication\resumes"
$errorLog = Join-Path $summaryDirectory "hook-errors.log"

try {
    $rawInput = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($rawInput)) {
        Write-HookResult
    }

    $eventData = $rawInput | ConvertFrom-Json
    if ([string]$eventData.hook_event_name -ne "Stop") {
        Write-HookResult
    }

    $message = [string]$eventData.last_assistant_message
    if ([string]::IsNullOrWhiteSpace($message)) {
        Write-HookResult
    }

    # Match accented or unaccented French markers while keeping this
    # PowerShell 5.1 source file ASCII-compatible.
    $startMarker = '(?:\p{So}\s*)?D(?:E|\u00C9)BUT\s+DU\s+R(?:E|\u00C9)SUM(?:E|\u00C9)'
    $endMarker = '(?:\p{So}\s*)?FIN\s+DU\s+(?:TERMINAL|R(?:E|\u00C9)SUM(?:E|\u00C9))'
    $summaryPattern = '(?is)' + $startMarker + '.*?' + $endMarker
    $summaryMatch = [regex]::Match($message, $summaryPattern)

    if (-not $summaryMatch.Success) {
        Write-HookResult
    }

    New-Item -ItemType Directory -Force -Path $summaryDirectory | Out-Null

    $sessionId = Get-SafeToken -Value $eventData.session_id -Fallback "session"
    $turnId = Get-SafeToken -Value $eventData.turn_id -Fallback "turn"
    $model = Get-SafeToken -Value $eventData.model -Fallback "model"
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss-fff"
    $createdAt = (Get-Date).ToString("o")
    $fileName = "${timestamp}_${sessionId}_${turnId}.md"
    $destination = Join-Path $summaryDirectory $fileName
    $temporary = "$destination.tmp"
    $latest = Join-Path $summaryDirectory "LATEST.md"

    $frontMatter = @(
        "---",
        "source: codex-stop-hook",
        "session_id: $sessionId",
        "turn_id: $turnId",
        "model: $model",
        "created_at: $createdAt",
        "---",
        ""
    ) -join "`r`n"

    $content = $frontMatter + $summaryMatch.Value.Trim() + "`r`n"

    Write-Utf8NoBom -Path $temporary -Content $content
    Move-Item -LiteralPath $temporary -Destination $destination -Force
    Copy-Item -LiteralPath $destination -Destination $latest -Force

    Write-HookResult
}
catch {
    try {
        New-Item -ItemType Directory -Force -Path $summaryDirectory | Out-Null
        $line = "{0} | {1}" -f (Get-Date).ToString("o"), $_.Exception.Message
        Add-Content -LiteralPath $errorLog -Value $line -Encoding UTF8
    }
    catch {
        # Never block Codex because the logging path itself failed.
    }

    Write-HookResult -SystemMessage "Le hook de resume Antmux a echoue; voir D:\communication\resumes\hook-errors.log."
}
