#requires -Version 5.1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-AntmuxRoot {
    if (-not [string]::IsNullOrWhiteSpace($env:ANTMUX_ROOT)) {
        return [System.IO.Path]::GetFullPath($env:ANTMUX_ROOT)
    }

    $moduleDirectory = Split-Path -Parent $PSScriptRoot
    return [System.IO.Path]::GetFullPath((Split-Path -Parent $moduleDirectory))
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

function Assert-AntmuxDrive {
    param([Parameter(Mandatory = $true)][string]$Root)

    $driveRoot = [System.IO.Path]::GetPathRoot($Root)
    $drive = New-Object System.IO.DriveInfo($driveRoot)
    if (-not $drive.IsReady) {
        throw "The Antmux drive is not ready: $driveRoot"
    }
    if ($drive.VolumeLabel -ine "Antmux") {
        throw "The drive must be named Antmux. Current label: '$($drive.VolumeLabel)'."
    }
}

function Get-ChatGPTBridgeConfig {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [string]$ConfigPath
    )

    if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
        $ConfigPath = Join-Path $Root "config\chatgpt-bridge.json"
    }

    $resolved = Resolve-AntmuxPath -Root $Root -Path $ConfigPath
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        throw "ChatGPT bridge configuration not found: $resolved"
    }

    $config = Get-Content -LiteralPath $resolved -Raw | ConvertFrom-Json
    foreach ($required in @(
        "title_contains",
        "display_device",
        "activation_delay_ms",
        "paste_delay_ms",
        "enter_delay_ms",
        "send_enter",
        "message_prefix",
        "message_suffix",
        "log_relative",
        "state_relative"
    )) {
        if ($null -eq $config.PSObject.Properties[$required]) {
            throw "Missing ChatGPT bridge configuration property: $required"
        }
    }

    return [pscustomobject]@{
        Path = $resolved
        Data = $config
    }
}

function Initialize-AntmuxWindowApi {
    if ("AntmuxWindowApi" -as [type]) {
        return
    }

    $source = @'
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;

public sealed class AntmuxWindowMatch
{
    public IntPtr Handle { get; set; }
    public string Title { get; set; }
    public string Device { get; set; }
    public int ProcessId { get; set; }
}

public static class AntmuxWindowApi
{
    private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [StructLayout(LayoutKind.Sequential)]
    private struct RECT
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    private struct MONITORINFOEX
    {
        public int cbSize;
        public RECT rcMonitor;
        public RECT rcWork;
        public uint dwFlags;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
        public string szDevice;
    }

    [DllImport("user32.dll")]
    private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);

    [DllImport("user32.dll")]
    private static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    private static extern int GetWindowTextLength(IntPtr hWnd);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

    [DllImport("user32.dll")]
    private static extern IntPtr MonitorFromWindow(IntPtr hWnd, uint flags);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    private static extern bool GetMonitorInfo(IntPtr monitor, ref MONITORINFOEX info);

    [DllImport("user32.dll")]
    private static extern bool ShowWindow(IntPtr hWnd, int command);

    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool BringWindowToTop(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern IntPtr SetFocus(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    private static extern bool AttachThreadInput(uint attach, uint attachTo, bool value);

    [DllImport("kernel32.dll")]
    private static extern uint GetCurrentThreadId();

    private const uint MONITOR_DEFAULTTONEAREST = 2;
    private const int SW_RESTORE = 9;

    private static string GetTitle(IntPtr hWnd)
    {
        int length = GetWindowTextLength(hWnd);
        if (length <= 0) return String.Empty;
        StringBuilder builder = new StringBuilder(length + 1);
        GetWindowText(hWnd, builder, builder.Capacity);
        return builder.ToString();
    }

    private static string GetDevice(IntPtr hWnd)
    {
        IntPtr monitor = MonitorFromWindow(hWnd, MONITOR_DEFAULTTONEAREST);
        if (monitor == IntPtr.Zero) return String.Empty;
        MONITORINFOEX info = new MONITORINFOEX();
        info.cbSize = Marshal.SizeOf(typeof(MONITORINFOEX));
        return GetMonitorInfo(monitor, ref info) ? info.szDevice : String.Empty;
    }

    public static AntmuxWindowMatch[] Find(string titleContains, string displayDevice)
    {
        List<AntmuxWindowMatch> matches = new List<AntmuxWindowMatch>();
        EnumWindows(delegate(IntPtr hWnd, IntPtr lParam)
        {
            if (!IsWindowVisible(hWnd)) return true;
            string title = GetTitle(hWnd);
            if (String.IsNullOrWhiteSpace(title)) return true;
            if (title.IndexOf(titleContains, StringComparison.OrdinalIgnoreCase) < 0) return true;

            string device = GetDevice(hWnd);
            if (!String.Equals(device, displayDevice, StringComparison.OrdinalIgnoreCase)) return true;

            uint processId;
            GetWindowThreadProcessId(hWnd, out processId);
            matches.Add(new AntmuxWindowMatch
            {
                Handle = hWnd,
                Title = title,
                Device = device,
                ProcessId = (int)processId
            });
            return true;
        }, IntPtr.Zero);
        return matches.ToArray();
    }

    public static AntmuxWindowMatch Describe(IntPtr hWnd)
    {
        uint processId;
        GetWindowThreadProcessId(hWnd, out processId);
        return new AntmuxWindowMatch
        {
            Handle = hWnd,
            Title = GetTitle(hWnd),
            Device = GetDevice(hWnd),
            ProcessId = (int)processId
        };
    }

    public static bool Activate(IntPtr hWnd)
    {
        ShowWindow(hWnd, SW_RESTORE);
        IntPtr foreground = GetForegroundWindow();

        uint ignored;
        uint targetThread = GetWindowThreadProcessId(hWnd, out ignored);
        uint foregroundThread = foreground == IntPtr.Zero ? 0 : GetWindowThreadProcessId(foreground, out ignored);
        uint currentThread = GetCurrentThreadId();

        bool attachedCurrent = false;
        bool attachedForeground = false;
        try
        {
            if (targetThread != 0 && currentThread != targetThread)
                attachedCurrent = AttachThreadInput(currentThread, targetThread, true);
            if (targetThread != 0 && foregroundThread != 0 && foregroundThread != targetThread)
                attachedForeground = AttachThreadInput(foregroundThread, targetThread, true);

            BringWindowToTop(hWnd);
            SetForegroundWindow(hWnd);
            SetFocus(hWnd);
        }
        finally
        {
            if (attachedForeground) AttachThreadInput(foregroundThread, targetThread, false);
            if (attachedCurrent) AttachThreadInput(currentThread, targetThread, false);
        }

        return GetForegroundWindow() == hWnd;
    }

    public static bool IsForeground(IntPtr hWnd)
    {
        return GetForegroundWindow() == hWnd;
    }
}
'@

    Add-Type -TypeDefinition $source -Language CSharp
}

function Get-AntmuxTextHash {
    param([Parameter(Mandatory = $true)][string]$Text)

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-", "")
    }
    finally {
        $sha.Dispose()
    }
}

function Set-AntmuxClipboardText {
    param([Parameter(Mandatory = $true)][string]$Text)

    $command = Get-Command Set-Clipboard -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        throw "Set-Clipboard is unavailable on this computer."
    }

    $lastError = $null
    for ($attempt = 0; $attempt -lt 10; $attempt++) {
        try {
            Set-Clipboard -Value $Text
            return
        }
        catch {
            $lastError = $_
            Start-Sleep -Milliseconds 150
        }
    }
    throw "The clipboard remained unavailable: $($lastError.Exception.Message)"
}

function Write-ChatGPTBridgeEvent {
    param(
        [Parameter(Mandatory = $true)][string]$LogPath,
        [Parameter(Mandatory = $true)][hashtable]$Data
    )

    $parent = Split-Path -Parent $LogPath
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $record = [ordered]@{
        timestamp = (Get-Date).ToString("o")
    }
    foreach ($key in $Data.Keys) {
        $record[$key] = $Data[$key]
    }
    Add-Content -LiteralPath $LogPath -Value (($record | ConvertTo-Json -Compress) + [Environment]::NewLine) -Encoding UTF8
}

function Test-ChatGPTBridgeTarget {
    [CmdletBinding()]
    param([string]$ConfigPath)

    $root = Get-AntmuxRoot
    Assert-AntmuxDrive -Root $root
    $configRecord = Get-ChatGPTBridgeConfig -Root $root -ConfigPath $ConfigPath
    $config = $configRecord.Data

    Initialize-AntmuxWindowApi
    $matches = [AntmuxWindowApi]::Find([string]$config.title_contains, [string]$config.display_device)

    return [pscustomobject]@{
        Status = if ($matches.Count -eq 1) { "ready" } elseif ($matches.Count -eq 0) { "not-found" } else { "ambiguous" }
        TitleContains = [string]$config.title_contains
        DisplayDevice = [string]$config.display_device
        MatchCount = $matches.Count
        Matches = @($matches | ForEach-Object { "$($_.Title) [$($_.Device)] PID=$($_.ProcessId)" })
    }
}

function Send-AntmuxToChatGPT {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$SummaryPath,
        [string]$ConfigPath,
        [switch]$TestOnly,
        [switch]$NoEnter,
        [switch]$Force
    )

    $root = Get-AntmuxRoot
    Assert-AntmuxDrive -Root $root
    $configRecord = Get-ChatGPTBridgeConfig -Root $root -ConfigPath $ConfigPath
    $config = $configRecord.Data

    $source = Resolve-AntmuxPath -Root $root -Path $SummaryPath
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Summary file not found: $source"
    }

    $content = Get-Content -LiteralPath $source -Raw
    if ([string]::IsNullOrWhiteSpace($content)) {
        throw "Summary file is empty: $source"
    }

    $hash = Get-AntmuxTextHash -Text $content
    $statePath = Resolve-AntmuxPath -Root $root -Path ([string]$config.state_relative)
    $logPath = Resolve-AntmuxPath -Root $root -Path ([string]$config.log_relative)

    if ((-not $Force) -and (Test-Path -LiteralPath $statePath -PathType Leaf)) {
        $sent = Get-Content -LiteralPath $statePath -ErrorAction SilentlyContinue
        if ($sent -contains $hash) {
            return [pscustomobject]@{
                Status = "already-sent"
                Source = $source
                Hash = $hash
            }
        }
    }

    Initialize-AntmuxWindowApi
    $matches = [AntmuxWindowApi]::Find([string]$config.title_contains, [string]$config.display_device)
    if ($matches.Count -eq 0) {
        Write-ChatGPTBridgeEvent -LogPath $logPath -Data @{ status = "blocked-not-found"; source = $source; hash = $hash }
        throw "No ChatGPT window was found on $($config.display_device). Move the intended ChatGPT window to Windows screen 3."
    }
    if ($matches.Count -gt 1) {
        Write-ChatGPTBridgeEvent -LogPath $logPath -Data @{ status = "blocked-ambiguous"; source = $source; hash = $hash; matches = $matches.Count }
        throw "More than one ChatGPT window was found on $($config.display_device). Leave exactly one there."
    }

    $target = $matches[0]
    if ($TestOnly) {
        return [pscustomobject]@{
            Status = "test-only"
            Source = $source
            Hash = $hash
            WindowTitle = $target.Title
            DisplayDevice = $target.Device
            ProcessId = $target.ProcessId
        }
    }

    $prefix = ([string]$config.message_prefix).Replace("{source}", [System.IO.Path]::GetFileName($source))
    $payload = $prefix + $content + [string]$config.message_suffix

    if (-not [AntmuxWindowApi]::Activate($target.Handle)) {
        Write-ChatGPTBridgeEvent -LogPath $logPath -Data @{ status = "blocked-activation"; source = $source; hash = $hash; title = $target.Title }
        throw "Windows refused to activate the selected ChatGPT window."
    }

    Start-Sleep -Milliseconds ([int]$config.activation_delay_ms)
    $verified = [AntmuxWindowApi]::Describe($target.Handle)
    if ((-not [AntmuxWindowApi]::IsForeground($target.Handle)) -or
        ($verified.Title.IndexOf([string]$config.title_contains, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) -or
        ($verified.Device -ine [string]$config.display_device)) {
        Write-ChatGPTBridgeEvent -LogPath $logPath -Data @{ status = "blocked-first-verification"; source = $source; hash = $hash }
        throw "ChatGPT lost focus or moved away from screen 3 before paste."
    }

    Set-AntmuxClipboardText -Text $payload
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    Start-Sleep -Milliseconds ([int]$config.paste_delay_ms)

    if ($NoEnter -or (-not [bool]$config.send_enter)) {
        Write-ChatGPTBridgeEvent -LogPath $logPath -Data @{ status = "pasted-not-sent"; source = $source; hash = $hash; title = $verified.Title }
        return [pscustomobject]@{
            Status = "pasted-not-sent"
            Source = $source
            Hash = $hash
            WindowTitle = $verified.Title
            DisplayDevice = $verified.Device
        }
    }

    Start-Sleep -Milliseconds ([int]$config.enter_delay_ms)
    $verified = [AntmuxWindowApi]::Describe($target.Handle)
    if ((-not [AntmuxWindowApi]::IsForeground($target.Handle)) -or
        ($verified.Title.IndexOf([string]$config.title_contains, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) -or
        ($verified.Device -ine [string]$config.display_device)) {
        Write-ChatGPTBridgeEvent -LogPath $logPath -Data @{ status = "blocked-before-enter"; source = $source; hash = $hash }
        throw "ChatGPT lost focus or moved away from screen 3 before Enter. The text was pasted but not sent."
    }

    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")

    $stateParent = Split-Path -Parent $statePath
    New-Item -ItemType Directory -Force -Path $stateParent | Out-Null
    Add-Content -LiteralPath $statePath -Value $hash -Encoding ASCII
    Write-ChatGPTBridgeEvent -LogPath $logPath -Data @{ status = "sent"; source = $source; hash = $hash; title = $verified.Title; display = $verified.Device }

    return [pscustomobject]@{
        Status = "sent"
        Source = $source
        Hash = $hash
        WindowTitle = $verified.Title
        DisplayDevice = $verified.Device
    }
}

Export-ModuleMember -Function @(
    "Send-AntmuxToChatGPT",
    "Test-ChatGPTBridgeTarget"
)
