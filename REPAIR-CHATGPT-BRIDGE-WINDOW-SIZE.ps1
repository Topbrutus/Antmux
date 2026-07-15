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
$changed = $false

$isIconicDeclaration = @'
    [DllImport("user32.dll")]
    private static extern bool IsIconic(IntPtr hWnd);
'@

$showWindowDeclaration = @'
    [DllImport("user32.dll")]
    private static extern bool ShowWindow(IntPtr hWnd, int command);
'@

if ($content -notmatch 'private static extern bool IsIconic\(IntPtr hWnd\);') {
    if (-not $content.Contains($showWindowDeclaration)) {
        throw "Could not find the ShowWindow declaration in $modulePath"
    }
    $content = $content.Replace(
        $showWindowDeclaration,
        $showWindowDeclaration + [Environment]::NewLine + [Environment]::NewLine + $isIconicDeclaration
    )
    $changed = $true
}

$oldActivation = @'
    public static bool Activate(IntPtr hWnd)
    {
        ShowWindow(hWnd, SW_RESTORE);
        IntPtr foreground = GetForegroundWindow();
'@

$newActivation = @'
    public static bool Activate(IntPtr hWnd)
    {
        // Preserve the current normal or maximized size. Restore only a minimized window.
        if (IsIconic(hWnd))
            ShowWindow(hWnd, SW_RESTORE);
        IntPtr foreground = GetForegroundWindow();
'@

if ($content.Contains($oldActivation)) {
    $content = $content.Replace($oldActivation, $newActivation)
    $changed = $true
}
elseif ($content -notmatch 'if \(IsIconic\(hWnd\)\)') {
    throw "Could not find the ChatGPT activation block in $modulePath"
}

if (-not $changed) {
    Write-Host "CHATGPT WINDOW SIZE REPAIR ALREADY APPLIED" -ForegroundColor Yellow
    Write-Host "Module : $modulePath"
    exit 0
}

$backupStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = "$modulePath.backup.windowsize.$backupStamp"
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

Write-Host "CHATGPT WINDOW SIZE REPAIRED" -ForegroundColor Green
Write-Host "Module : $modulePath"
Write-Host "Backup : $backupPath"
Write-Host "Rule   : Restore ChatGPT only when it is minimized; preserve maximized size otherwise."
