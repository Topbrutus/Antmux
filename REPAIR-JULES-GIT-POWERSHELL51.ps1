#requires -Version 5.1

[CmdletBinding()]
param([string]$Root)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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

$modulePath = Join-Path $Root "modules\jules\Jules.SummaryPublisher.psm1"
if (-not (Test-Path -LiteralPath $modulePath -PathType Leaf)) {
    throw "Jules module not found: $modulePath"
}

$content = Get-Content -LiteralPath $modulePath -Raw
if ($content.Contains('$previousErrorActionPreference = $ErrorActionPreference')) {
    Write-Host "JULES GIT COMPATIBILITY ALREADY REPAIRED" -ForegroundColor Green
    Write-Host "Module: $modulePath"
    exit 0
}

$oldBlock = @'
    $previousPrompt = $env:GIT_TERMINAL_PROMPT
    $env:GIT_TERMINAL_PROMPT = "1"
    try {
        Push-Location -LiteralPath $WorkingDirectory
        try {
            $output = (& $Git @Arguments 2>&1 | Out-String).Trim()
            $exitCode = $LASTEXITCODE
        }
        finally {
            Pop-Location
        }
    }
    finally {
        $env:GIT_TERMINAL_PROMPT = $previousPrompt
    }
'@

$newBlock = @'
    $previousPrompt = $env:GIT_TERMINAL_PROMPT
    $previousErrorActionPreference = $ErrorActionPreference
    $env:GIT_TERMINAL_PROMPT = "1"
    $exitCode = -1
    $output = ""
    try {
        # Windows PowerShell 5.1 turns native stderr into ErrorRecord objects.
        # Git writes normal progress messages such as "From ..." to stderr,
        # so only Git's numeric exit code may decide success or failure.
        $ErrorActionPreference = "Continue"
        Push-Location -LiteralPath $WorkingDirectory
        try {
            $records = & $Git @Arguments 2>&1
            $exitCode = $LASTEXITCODE
            $output = ($records | ForEach-Object { $_.ToString() } | Out-String).Trim()
        }
        finally {
            Pop-Location
        }
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
        $env:GIT_TERMINAL_PROMPT = $previousPrompt
    }
'@

if (-not $content.Contains($oldBlock)) {
    throw "The expected Invoke-JulesGit block was not found. No file was changed."
}

$backupStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = "$modulePath.backup.gitcompat.$backupStamp"
Copy-Item -LiteralPath $modulePath -Destination $backupPath -Force

$updated = $content.Replace($oldBlock, $newBlock)
[System.IO.File]::WriteAllText(
    $modulePath,
    $updated,
    (New-Object System.Text.UTF8Encoding($false))
)

$tokens = $null
$errors = $null
$null = [System.Management.Automation.Language.Parser]::ParseFile(
    $modulePath,
    [ref]$tokens,
    [ref]$errors
)

if ($errors.Count -gt 0) {
    Copy-Item -LiteralPath $backupPath -Destination $modulePath -Force
    throw "PowerShell syntax validation failed; the backup was restored: $($errors[0].Message)"
}

Write-Host "" 
Write-Host "JULES GIT COMPATIBILITY REPAIRED" -ForegroundColor Green
Write-Host "Module : $modulePath"
Write-Host "Backup : $backupPath"
Write-Host "Rule   : Git stderr is informational unless Git returns a non-zero exit code."
