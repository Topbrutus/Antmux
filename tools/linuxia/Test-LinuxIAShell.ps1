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
    $framesModule = Join-Path $root 'shell/frames.py'
    $renderModule = Join-Path $root 'shell/render.py'
    $greetingsModule = Join-Path $root 'shell/greetings.py'
    $conversationModule = Join-Path $root 'shell/conversation.py'
    $assetRoot = Join-Path $root 'shell/assets'
    $assetPaths = @((Join-Path $assetRoot 'manifest.json'))
    $assetPaths += @(0..9 | ForEach-Object {
        Join-Path $assetRoot ('frames-{0:00}.json' -f $_)
    })
    $rootLauncher = Join-Path $root '../linuxia.ps1'

    Write-Host 'ANTMUX LINUXIA SHELL VALIDATOR'
    Write-Host "CLI_ROOT: $root"
    Write-Host 'MODE: INTERPRETER_RECEPTION_LAYOUT_GUARDED'

    $requiredPaths = @(
        $scriptPath,
        $framesModule,
        $renderModule,
        $greetingsModule,
        $conversationModule,
        $rootLauncher
    ) + @($assetPaths)
    foreach ($required in $requiredPaths) {
        Add-ShellTestResult `
            ('FILE-' + ([IO.Path]::GetFileName($required) -replace '[^A-Za-z0-9]', '_').ToUpperInvariant()) `
            (Test-Path -LiteralPath $required -PathType Leaf) `
            "Required file exists: $required"
    }

    $scriptText = @($scriptPath, $framesModule, $renderModule, $greetingsModule, $conversationModule) |
        ForEach-Object { Get-Content -LiteralPath $_ -Raw -Encoding UTF8 } |
        Out-String
    $conversationText = Get-Content -LiteralPath $conversationModule -Raw -Encoding UTF8
    $consoleText = Get-Content -LiteralPath $scriptPath -Raw -Encoding UTF8

    Add-ShellTestResult 'FRAMES-LOCAL-ASSETS' `
        (@($assetPaths | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }).Count -eq 11) `
        'Manifest and ten local champion-frame resources are present'

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

    Add-ShellTestResult 'STATIC-NETWORK' `
        (-not ($scriptText -match '(?i)urllib|requests|http\.client|socket\.|Invoke-WebRequest|Invoke-RestMethod')) `
        'No network client is present in the shell runtime'
    Add-ShellTestResult 'STATIC-MODEL-EXACT' `
        ($conversationText -match 'MODEL_NAME\s*=\s*"linuxia-interprete:4b"') `
        'The reception model name is exact'
    $listPreflightIndex = $conversationText.IndexOf('[executable, "list"]')
    $thinkPreflightIndex = $conversationText.IndexOf('[executable, "run", "--help"]')
    $inferenceLaunchIndex = $conversationText.IndexOf('process = subprocess.Popen')
    Add-ShellTestResult 'STATIC-MODEL-PREFLIGHT' `
        (($listPreflightIndex -ge 0) -and `
         ($thinkPreflightIndex -gt $listPreflightIndex) -and `
         ($inferenceLaunchIndex -gt $thinkPreflightIndex)) `
        'Installed-model and thinking-control preflights occur before inference'
    Add-ShellTestResult 'STATIC-THINK-DISABLED' `
        ($conversationText -match 'OLLAMA_THINK_ARGUMENT\s*=\s*"--think=false"' -and `
         $conversationText -match '"run",\s*MODEL_NAME,\s*OLLAMA_THINK_ARGUMENT') `
        'Internal reasoning output is disabled explicitly at the Ollama CLI boundary'
    Add-ShellTestResult 'STATIC-NO-AUTO-MODEL-MUTATION' `
        (-not ($conversationText -match '(?i)["''](?:pull|serve|create|rm|cp)["'']')) `
        'No pull, serve, create, remove or copy model command exists'
    Add-ShellTestResult 'STATIC-NO-SHELL-EXECUTION' `
        (-not ($conversationText -match '(?i)shell\s*=\s*true')) `
        'Model process uses an argument vector, not a command shell'
    Add-ShellTestResult 'STATIC-CONVERSATION-NO-FILES' `
        (-not ($conversationText -match '(?i)\bopen\s*\(|write_text|write_bytes|FileStream|Remove-Item')) `
        'The reception model layer has no file read/write primitive'
    Add-ShellTestResult 'STATIC-DELETE' `
        (-not ($scriptText -match '(?i)shutil\.rmtree|Path\.unlink|os\.remove')) `
        'No deletion primitive is present in the shell runtime'
    Add-ShellTestResult 'STATIC-FLASHING-STATUS' `
        (-not ($scriptText -match '(?m)^\s*(status|tail)\s*=')) `
        'No flashing status line is present'
    Add-ShellTestResult 'STATIC-FIXED-CURSOR' `
        ($scriptText -match 'cursor_home\(\)' -and $scriptText -match 'no_trailing_newline') `
        'Renderer reuses one fixed terminal surface'
    Add-ShellTestResult 'STATIC-LINE-CLEAR' `
        ($scriptText.Contains('sys.stdout.write("\x1b[2K")') -and `
         $scriptText.Contains('sys.stdout.write("\x1b[J")')) `
        'Every rendered row clears stale input and resized-screen remnants'
    Add-ShellTestResult 'STATIC-OUTPUT-WRAP' `
        ($scriptText -match 'wrap_transcript_line' -and `
         $scriptText -match 'visible_transcript_lines' -and `
         $scriptText -match 'compact_output_rows') `
        'The log wraps words above a stable compact animation viewport'
    Add-ShellTestResult 'STATIC-CANNED-GREETING-REMOVED' `
        (-not ($scriptText -match 'Bonjour Gabi\. Je suis prête\.|Salut Gabi\. Je suis prête\.')) `
        'Prepared greeting responses are absent'
    Add-ShellTestResult 'STATIC-NATURAL-LANGUAGE-INTERPRETER' `
        ($consoleText -match 'Toute phrase ordinaire' -and $consoleText -match 'run_conversation_with_animation') `
        'Ordinary sentences, including greetings, are routed to LinuxIA Interprète'
    Add-ShellTestResult 'STATIC-LANGUAGE-MODES' `
        ($scriptText -match '/langage court\|normal\|long\|auto' -and $conversationText -match 'LANGUAGE_MODES') `
        'Custom response-length commands are connected'
    Add-ShellTestResult 'STATIC-HISTORY-BOUNDED' `
        ($consoleText -match 'history\s*=\s*history\[-6:\]') `
        'In-memory conversation context is bounded'
    Add-ShellTestResult 'STATIC-LOG-BUFFER-4000' `
        ($consoleText -match 'TRANSCRIPT_LINE_LIMIT\s*=\s*4000' -and `
         $consoleText -match 'maxlen=TRANSCRIPT_LINE_LIMIT' -and `
         $consoleText -match 'transcript_buffer_4000') `
        'The in-memory terminal log retains exactly 4000 logical lines'
    Add-ShellTestResult 'STATIC-PROVISIONAL-STREAM' `
        ($conversationText -match 'class ProvisionalResponseBuffer' -and `
         $consoleText -match 'provisional_transcript = list\(transcript\)' -and `
         $consoleText -match 'final_output = stream\.finalize\(\)') `
        'Streaming fragments remain provisional until a safe boundary or final event'
    Add-ShellTestResult 'STATIC-ANTI-STUTTER' `
        ($conversationText -match '_apply_backspaces' -and `
         $conversationText -match '_remove_adjacent_word_stutter') `
        'Terminal edits and accidental adjacent word stutters are normalized'
    Add-ShellTestResult 'STATIC-LOG-VIEWPORT' `
        ($scriptText -match 'PREFERRED_OUTPUT_ROWS_MIN\s*=\s*8' -and `
         $scriptText -match 'visible_log_rows_at_least_10') `
        'A standard terminal reserves at least ten visible rows for the log'
    Add-ShellTestResult 'STATIC-SYSTEM-JOB-HONEST' `
        ($scriptText -match 'SYSTEM_JOB: NOT_CONNECTED' -and $conversationText -match 'SYSTEM_JOB_STATE\s*=\s*"NOT_CONNECTED"') `
        'The reception layer does not pretend that System Job is connected'

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
        $pythonArguments += '-B'
        $pythonArguments += @($scriptPath, 'self-test')
        $output = @(& $pythonCommand.Source @pythonArguments 2>&1)
        $exitCode = $LASTEXITCODE
        Add-ShellTestResult 'SELFTEST-EXIT' ($exitCode -eq 0) 'Python self-test exits successfully'

        $jsonLine = [string]($output | Select-Object -Last 1)
        $selfTest = $jsonLine | ConvertFrom-Json
        Add-ShellTestResult 'SELFTEST-RESULT' ([bool]$selfTest.ok) 'Python fixed-render checks all pass'
        Add-ShellTestResult 'SELFTEST-FRAMES' ([int]$selfTest.frame_count -eq 36) 'Python loads exactly 36 champion frames'
        Add-ShellTestResult 'SELFTEST-CONVERSATION' ([bool]$selfTest.conversation_ok) 'LinuxIA Interprète reception logic checks all pass'
        Add-ShellTestResult 'SELFTEST-CANNED-REMOVED' ([bool]$selfTest.canned_greetings_removed) 'Prepared greeting library is disabled'
    }

    $ollamaCommand = Get-Command ollama.exe -ErrorAction SilentlyContinue
    if ($null -eq $ollamaCommand) {
        $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
    }
    Add-ShellTestResult 'ENV-OLLAMA' ($null -ne $ollamaCommand) 'Ollama command is available'
    if ($null -ne $ollamaCommand) {
        $ollamaList = @(& $ollamaCommand.Source list 2>&1)
        $ollamaExit = $LASTEXITCODE
        Add-ShellTestResult 'ENV-OLLAMA-LIST' ($ollamaExit -eq 0) 'Ollama model list is readable'
        $modelPresent = (($ollamaList -join "`n") -match '(?im)^linuxia-interprete:4b\s+')
        Add-ShellTestResult 'ENV-LINUXIA-INTERPRETER-4B' $modelPresent 'linuxia-interprete:4b is already installed'
        $ollamaRunHelp = @(& $ollamaCommand.Source run --help 2>&1)
        $ollamaHelpExit = $LASTEXITCODE
        $thinkAvailable = ($ollamaHelpExit -eq 0) -and (($ollamaRunHelp -join "`n") -match '--think')
        Add-ShellTestResult 'ENV-OLLAMA-THINK-CONTROL' $thinkAvailable 'Ollama exposes explicit --think control'
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
