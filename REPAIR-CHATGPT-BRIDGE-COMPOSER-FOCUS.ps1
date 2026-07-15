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

$focusFunction = @'
function Focus-AntmuxChatGPTComposer {
    param([Parameter(Mandatory = $true)][IntPtr]$WindowHandle)

    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes

    $rootElement = [System.Windows.Automation.AutomationElement]::FromHandle($WindowHandle)
    if ($null -eq $rootElement) {
        throw "Windows UI Automation could not inspect the selected ChatGPT window."
    }

    $rootRect = $rootElement.Current.BoundingRectangle
    $rootProcessId = $rootElement.Current.ProcessId
    $all = $rootElement.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.Condition]::TrueCondition
    )

    $candidates = New-Object System.Collections.Generic.List[object]
    for ($index = 0; $index -lt $all.Count; $index++) {
        $element = $all.Item($index)
        try {
            $current = $element.Current
            if ((-not $current.IsEnabled) -or $current.IsOffscreen -or (-not $current.IsKeyboardFocusable)) {
                continue
            }

            $controlType = $current.ControlType
            $isTextControl =
                ($controlType -eq [System.Windows.Automation.ControlType]::Edit) -or
                ($controlType -eq [System.Windows.Automation.ControlType]::Document) -or
                ($controlType -eq [System.Windows.Automation.ControlType]::Custom)
            if (-not $isTextControl) {
                continue
            }

            $rect = $current.BoundingRectangle
            if ($rect.IsEmpty -or ($rect.Width -lt 180) -or ($rect.Height -lt 18)) {
                continue
            }
            if ($rect.Top -lt ($rootRect.Top + ($rootRect.Height * 0.45))) {
                continue
            }

            $name = [string]$current.Name
            $score = [double]$rect.Bottom
            if ($controlType -eq [System.Windows.Automation.ControlType]::Edit) {
                $score += 100000
            }
            elseif ($controlType -eq [System.Windows.Automation.ControlType]::Document) {
                $score += 50000
            }
            if ($name -match '(?i)chatgpt|message|prompt|demander|ask|envoyer|send') {
                $score += 200000
            }
            $score += [Math]::Min($rect.Width, 5000)

            $candidates.Add([pscustomobject]@{
                Element = $element
                Score = $score
                Name = $name
                ControlType = $controlType.ProgrammaticName
                Left = $rect.Left
                Top = $rect.Top
                Width = $rect.Width
                Height = $rect.Height
            })
        }
        catch {
            continue
        }
    }

    if ($candidates.Count -eq 0) {
        throw "No editable ChatGPT composer was exposed through Windows UI Automation. The bridge stopped before paste."
    }

    $selected = $candidates | Sort-Object Score -Descending | Select-Object -First 1
    $selected.Element.SetFocus()
    Start-Sleep -Milliseconds 250

    $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
    if (($null -eq $focused) -or ($focused.Current.ProcessId -ne $rootProcessId)) {
        throw "Windows did not keep keyboard focus inside the selected ChatGPT application."
    }

    return [pscustomobject]@{
        Name = $selected.Name
        ControlType = $selected.ControlType
        Left = $selected.Left
        Top = $selected.Top
        Width = $selected.Width
        Height = $selected.Height
    }
}

'@

if ($content -notmatch 'function Focus-AntmuxChatGPTComposer') {
    $anchor = 'function Send-AntmuxToChatGPT {'
    if (-not $content.Contains($anchor)) {
        throw "Could not find Send-AntmuxToChatGPT in $modulePath"
    }
    $content = $content.Replace($anchor, $focusFunction + $anchor)
}

$oldPaste = @'
    Set-AntmuxClipboardText -Text $payload
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.SendKeys]::SendWait("^v")
'@

$newPaste = @'
    Set-AntmuxClipboardText -Text $payload
    $composer = Focus-AntmuxChatGPTComposer -WindowHandle $target.Handle
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.SendKeys]::SendWait("^v")
'@

if ($content.Contains($oldPaste)) {
    $content = $content.Replace($oldPaste, $newPaste)
}
elseif ($content -notmatch '\$composer\s*=\s*Focus-AntmuxChatGPTComposer') {
    throw "Could not find the ChatGPT paste block in $modulePath"
}

if ($content -eq $original) {
    Write-Host "CHATGPT COMPOSER FOCUS REPAIR ALREADY APPLIED" -ForegroundColor Yellow
    Write-Host "Module : $modulePath"
    exit 0
}

$backupStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = "$modulePath.backup.composerfocus.$backupStamp"
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

Write-Host "CHATGPT COMPOSER FOCUS REPAIRED" -ForegroundColor Green
Write-Host "Module : $modulePath"
Write-Host "Backup : $backupPath"
Write-Host "Rule   : Focus an editable ChatGPT control through Windows UI Automation before Ctrl+V."
Write-Host "Safety : Stop before paste when no suitable composer is exposed."
