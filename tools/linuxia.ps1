Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$all = @($args)
if ($all.Count -gt 0 -and ([string]$all[0]).ToLowerInvariant() -eq 'shell') {
    $cliRoot = Join-Path $PSScriptRoot 'linuxia'
    $shellScript = Join-Path $cliRoot 'shell/linuxia_ant_console.py'
    $repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path

    if (-not (Test-Path -LiteralPath $shellScript -PathType Leaf)) {
        Write-Error "LINUXIA_SHELL_MISSING: $shellScript"
        exit 5
    }

    $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    $pythonArguments = @()
    if ($null -eq $pythonCommand) {
        $pythonCommand = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($null -ne $pythonCommand) {
            $pythonArguments += '-3'
        }
    }
    if ($null -eq $pythonCommand) {
        Write-Error 'LINUXIA_SHELL_PYTHON_MISSING: Python 3 est requis pour le mode shell.'
        exit 5
    }

    $pythonArguments += '-B'
    $pythonArguments += @(
        $shellScript,
        'shell',
        '--repo',
        $repoRoot
    )
    $pythonArguments += @($all | Select-Object -Skip 1)

    & $pythonCommand.Source @pythonArguments
    exit $LASTEXITCODE
}

$launcher = Join-Path $PSScriptRoot 'linuxia/cli.ps1'
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    Write-Error "LINUXIA_LAUNCHER_MISSING: $launcher"
    exit 4
}
& $launcher @args
exit $LASTEXITCODE
