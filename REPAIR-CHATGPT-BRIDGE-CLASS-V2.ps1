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

$modulePath = Join-Path $Root "modules\chatgpt-bridge\ChatGPT.Bridge.psm1"
if (-not (Test-Path -LiteralPath $modulePath -PathType Leaf)) {
    throw "ChatGPT bridge module not found: $modulePath"
}

$content = Get-Content -LiteralPath $modulePath -Raw
$original = $content

# Version both generated C# types so an old class already loaded in the current
# PowerShell process cannot mask the corrected implementation.
$content = [regex]::Replace($content, '\bAntmuxWindowMatch\b', 'AntmuxWindowMatchV2')
$content = [regex]::Replace($content, '\bAntmuxWindowApi\b', 'AntmuxWindowApiV2')

$showWindowDeclaration = @'
    [DllImport("user32.dll")]
    private static extern bool ShowWindow(IntPtr hWnd, int command);
'@

$isIconicDeclaration = @'
    [DllImport("user32.dll")]
    private static extern bool IsIconic(IntPtr hWnd);
'@

if ($content -notmatch 'private static extern bool IsIconic\(IntPtr hWnd\);') {
    if (-not $content.Contains($showWindowDeclaration)) {
        throw "Could not find the ShowWindow declaration in $modulePath"
    }
    $content = $content.Replace(
        $showWindowDeclaration,
        $showWindowDeclaration + [Environment]::NewLine + [Environment]::NewLine + $isIconicDeclaration
    )
}

if ($content -notmatch 'if \(IsIconic\(hWnd\)\)') {
    $oldActivationLine = '        ShowWindow(hWnd, SW_RESTORE);'
    $newActivationLines = @'
        // Preserve the current normal or maximized geometry.
        // Restore the window only when Windows reports it as minimized.
        if (IsIconic(hWnd))
            ShowWindow(hWnd, SW_RESTORE);
'@
    if (-not $content.Contains($oldActivationLine)) {
        throw "Could not find the ChatGPT activation line in $modulePath"
    }
    $content = $content.Replace($oldActivationLine, $newActivationLines)
}

if ($content -eq $original) {
    Write-Host "CHATGPT BRIDGE V2 ALREADY APPLIED" -ForegroundColor Yellow
    Write-Host "Module : $modulePath"
    exit 0
}

$backupStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = "$modulePath.backup.classv2.$backupStamp"
Copy-Item -LiteralPath $modulePath -Destination $backupPath -Force
Set-Content -LiteralPath $modulePath -Value $content -Encoding UTF8

$tokens = $null
$errors = $null
$null = [System.Management.Automation.Language.Parser]::ParseFile(
    $modulePath,
    [ref]$tokens,
    [ref]$errors
)
if ($errors.Count -gt 0) {
    Copy-Item -LiteralPath $backupPath -Destination $modulePath -Force
    throw "PowerShell syntax validation failed; the original module was restored: $($errors[0].Message)"
}

Write-Host "CHATGPT BRIDGE WINDOW API V2 INSTALLED" -ForegroundColor Green
Write-Host "Module : $modulePath"
Write-Host "Backup : $backupPath"
Write-Host "Rule   : The current PowerShell session must load V2; ChatGPT geometry is preserved unless minimized."
