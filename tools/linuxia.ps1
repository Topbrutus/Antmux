$launcher = Join-Path $PSScriptRoot 'linuxia/cli.ps1'
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    Write-Error "LINUXIA_LAUNCHER_MISSING: $launcher"
    exit 4
}
& $launcher @args
exit $LASTEXITCODE
