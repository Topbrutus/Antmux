#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$Root,
    [int]$ComposerX = -861,
    [int]$ComposerY = 976
)

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
$configPath = Join-Path $Root "config\chatgpt-bridge.json"
if (-not (Test-Path -LiteralPath $modulePath -PathType Leaf)) {
    throw "ChatGPT bridge module not found: $modulePath"
}
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "ChatGPT bridge configuration not found: $configPath"
}

$backupStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$moduleBackup = "$modulePath.backup.calibratedclick.$backupStamp"
$configBackup = "$configPath.backup.calibratedclick.$backupStamp"
Copy-Item -LiteralPath $modulePath -Destination $moduleBackup -Force
Copy-Item -LiteralPath $configPath -Destination $configBackup -Force

$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$config | Add-Member -MemberType NoteProperty -Name composer_click_x -Value $ComposerX -Force
$config | Add-Member -MemberType NoteProperty -Name composer_click_y -Value $ComposerY -Force
$config | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $configPath -Encoding UTF8

$content = Get-Content -LiteralPath $modulePath -Raw
$original = $content

$clickFunction = @'
function Invoke-AntmuxCalibratedComposerClick {
    param(
        [Parameter(Mandatory = $true)][IntPtr]$WindowHandle,
        [Parameter(Mandatory = $true)][int]$X,
        [Parameter(Mandatory = $true)][int]$Y
    )

    if (-not ("AntmuxCalibratedMouseV1" -as [type])) {
        Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class AntmuxCalibratedMouseV1
{
    [StructLayout(LayoutKind.Sequential)]
    private struct POINT
    {
        public int X;
        public int Y;
    }

    [DllImport("user32.dll")]
    private static extern bool SetCursorPos(int x, int y);

    [DllImport("user32.dll")]
    private static extern IntPtr WindowFromPoint(POINT point);

    [DllImport("user32.dll")]
    private static extern IntPtr GetAncestor(IntPtr hWnd, uint flags);

    [DllImport("user32.dll")]
    private static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extraInfo);

    private const uint GA_ROOT = 2;
    private const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    private const uint MOUSEEVENTF_LEFTUP = 0x0004;

    public static bool PointBelongsToWindow(IntPtr expectedRoot, int x, int y)
    {
        POINT point = new POINT { X = x, Y = y };
        IntPtr child = WindowFromPoint(point);
        if (child == IntPtr.Zero) return false;
        IntPtr root = GetAncestor(child, GA_ROOT);
        return root == expectedRoot;
    }

    public static bool Click(IntPtr expectedRoot, int x, int y)
    {
        if (!PointBelongsToWindow(expectedRoot, x, y)) return false;
        if (!SetCursorPos(x, y)) return false;
        mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, UIntPtr.Zero);
        mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, UIntPtr.Zero);
        return true;
    }
}
"@ -Language CSharp
    }

    if (-not [AntmuxCalibratedMouseV1]::PointBelongsToWindow($WindowHandle, $X, $Y)) {
        throw "The calibrated composer point ($X,$Y) is no longer inside the selected ChatGPT window. The bridge stopped before clicking."
    }

    if (-not [AntmuxCalibratedMouseV1]::Click($WindowHandle, $X, $Y)) {
        throw "Windows could not click the calibrated ChatGPT composer point ($X,$Y)."
    }

    Start-Sleep -Milliseconds 350
}

'@

if ($content -notmatch 'function Invoke-AntmuxCalibratedComposerClick') {
    $anchor = 'function Send-AntmuxToChatGPT {'
    if (-not $content.Contains($anchor)) {
        Copy-Item -LiteralPath $moduleBackup -Destination $modulePath -Force
        Copy-Item -LiteralPath $configBackup -Destination $configPath -Force
        throw "Could not find Send-AntmuxToChatGPT in $modulePath"
    }
    $content = $content.Replace($anchor, $clickFunction + $anchor)
}

$pastePattern = '(?ms)    Set-AntmuxClipboardText -Text \$payload\r?\n(?:    \$composer = Focus-AntmuxChatGPTComposer -WindowHandle \$target\.Handle\r?\n)?    Add-Type -AssemblyName System\.Windows\.Forms\r?\n    \[System\.Windows\.Forms\.SendKeys\]::SendWait\("\^v"\)'
$newPaste = @'
    Set-AntmuxClipboardText -Text $payload
    Invoke-AntmuxCalibratedComposerClick `
        -WindowHandle $target.Handle `
        -X ([int]$config.composer_click_x) `
        -Y ([int]$config.composer_click_y)
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.SendKeys]::SendWait("^v")
'@

if ([regex]::IsMatch($content, $pastePattern)) {
    $content = [regex]::Replace($content, $pastePattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($match) $newPaste }, 1)
}
elif ($content -notmatch 'Invoke-AntmuxCalibratedComposerClick') {
    Copy-Item -LiteralPath $moduleBackup -Destination $modulePath -Force
    Copy-Item -LiteralPath $configBackup -Destination $configPath -Force
    throw "Could not find the ChatGPT paste block in $modulePath"
}

Set-Content -LiteralPath $modulePath -Value $content -Encoding UTF8

$tokens = $null
$errors = $null
$null = [System.Management.Automation.Language.Parser]::ParseFile(
    $modulePath,
    [ref]$tokens,
    [ref]$errors
)
if ($errors.Count -gt 0) {
    Copy-Item -LiteralPath $moduleBackup -Destination $modulePath -Force
    Copy-Item -LiteralPath $configBackup -Destination $configPath -Force
    throw "PowerShell syntax validation failed; original files restored: $($errors[0].Message)"
}

Write-Host "CHATGPT CALIBRATED COMPOSER CLICK INSTALLED" -ForegroundColor Green
Write-Host "Module : $modulePath"
Write-Host "Config : $configPath"
Write-Host "Point  : X=$ComposerX Y=$ComposerY"
Write-Host "Backup : $moduleBackup"
Write-Host "Safety : The point must still belong to the selected ChatGPT window or the bridge stops before paste."
