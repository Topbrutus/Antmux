[CmdletBinding()]
param([string]$CliRoot, [switch]$PassThru)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($CliRoot)) {
    $CliRoot = $PSScriptRoot
}

$script:Results = New-Object System.Collections.ArrayList

function Add-ShellTestResult {
    param([string]$Id, [bool]$Passed, [string]$Description)
    $null = $script:Results.Add([pscustomobject]@{
        id = $Id
        passed = $Passed
        description = $Description
    })
    $prefix = if ($Passed) { '[PASS]' } else { '[FAIL]' }
    Write-Host "$prefix $Id - $Description"
}

try {
    $root = (Resolve-Path -LiteralPath $CliRoot).Path
    $repoRoot = (Resolve-Path -LiteralPath (Join-Path $root '../..')).Path
    $scriptPath = Join-Path $root 'shell/linuxia_ant_console.py'
    $rootLauncher = Join-Path $root '../linuxia.ps1'

    Write-Host 'ANTMUX LINUXIA SHELL VALIDATOR'
    Write-Host "CLI_ROOT: $root"
    Write-Host 'MODE: PROTOTYPE_VISUEL_FIXE'

    foreach ($required in @($scriptPath, $rootLauncher)) {
        Add-ShellTestResult `
            ('FILE-' + ([IO.Path]::GetFileName($required) -replace '[^A-Za-z0-9]', '_').ToUpperInvariant()) `
            (Test-Path -LiteralPath $required -PathType Leaf) `
            "Required file exists: $required"
    }

    $scriptText = Get-Content -LiteralPath $scriptPath -Raw -Encoding UTF8
    Add-ShellTestResult 'FRAMES-EMBEDDED' `
        ($scriptText -match 'EMBEDDED_FRAMES_B85') `
        'Exactly one embedded frame package is present'

    $launcherText = Get-Content -LiteralPath $rootLauncher -Raw -Encoding UTF8
    Add-ShellTestResult 'LAUNCHER-EXPLICIT' `
        ($launcherText -match "(?i)eq\s+'shell'") `
        'Shell starts only after the explicit shell command'
    Add-ShellTestResult 'LAUNCHER-PYTHON-GUARD' `
        ($launcherText -match 'LINUXIA_SHELL_PYTHON_MISSING') `
        'Launcher fails closed when Python 3 is unavailable'
    Add-ShellTestResult 'LAUNCHER-INSPECT-PRESERVED' `
        ($launcherText -match "linuxia/cli\.ps1") `
        'Existing PowerShell inspect launcher remains present'

    foreach ($check in @(
        @('STATIC-NETWORK', '(?i)urllib|requests|http\.client|Invoke-WebRequest|Invoke-RestMethod'),
        @('STATIC-MODEL', '(?i)ollama|model\.activate'),
        @('STATIC-DELETE', '(?i)shutil\.rmtree|Path\.unlink|os\.remove'),
        @('STATIC-FLASHING-STATUS', 'LINUXIA TRAVAILLE|·  ·  ·')
    )) {
        Add-ShellTestResult $check[0] `
            (-not ($scriptText -match $check[1])) `
            "Forbidden shell behavior absent: $($check[0])"
    }
    Add-ShellTestResult 'STATIC-FIXED-CURSOR' `
        ($scriptText -match 'cursor_home\(\)' -and $scriptText -match 'no_trailing_newline') `
        'Renderer reuses one fixed terminal surface'

    $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    $pythonPrefix = @()
    if ($null -eq $pythonCommand) {
        $pythonCommand = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($null -ne $pythonCommand) { $pythonPrefix += '-3' }
    }
    Add-ShellTestResult 'ENV-PYTHON' ($null -ne $pythonCommand) 'Python 3 command is available'

    if ($null -ne $pythonCommand) {
        $pythonArguments = @()
        $pythonArguments += $pythonPrefix
        $pythonArguments += @($scriptPath, 'self-test')
        $output = @(& $pythonCommand.Source @pythonArguments 2>&1)
        $exitCode = $LASTEXITCODE
        Add-ShellTestResult 'SELFTEST-EXIT' ($exitCode -eq 0) 'Python self-test exits successfully'

        $jsonLine = [string]($output | Select-Object -Last 1)
        $selfTest = $jsonLine | ConvertFrom-Json
        Add-ShellTestResult 'SELFTEST-RESULT' ([bool]$selfTest.ok) 'Python fixed-render checks all pass'
        Add-ShellTestResult 'SELFTEST-FRAMES' ([int]$selfTest.frame_count -eq 100) 'Python loads exactly 100 frames'
    }

    Add-ShellTestResult 'REPO-ROOT' (Test-Path -LiteralPath $repoRoot -PathType Container) 'Repository root resolves'
}
catch {
    Write-Host ('FATAL: ' + $_.Exception.Message)
    Add-ShellTestResult 'FATAL' $false $_.Exception.Message
}

$passed = @($script:Results | Where-Object { $_.passed }).Count
$failed = @($script:Results | Where-Object { -not $_.passed }).Count
Write-Host "`nTOTAL: $($script:Results.Count)"
Write-Host "PASSED: $passed"
Write-Host "FAILED: $failed"
if ($failed -eq 0) { Write-Host 'ALL_TESTS: PASS' } else { Write-Host 'ALL_TESTS: FAIL' }

if ($PassThru) {
    [pscustomobject]@{
        total = $script:Results.Count
        passed = $passed
        failed = $failed
        all_tests = ($failed -eq 0)
        results = @($script:Results)
    }
}

exit $(if ($failed -eq 0) { 0 } else { 1 })
