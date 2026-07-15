#requires -Version 5.1

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SummaryPath,
    [string]$ProjectId,
    [string]$JobId,
    [string]$ConfigPath,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$modulePath = Join-Path $PSScriptRoot "Jules.SummaryPublisher.psm1"
$module = Import-Module -Name $modulePath -Force -PassThru

# Windows PowerShell 5.1 can promote ordinary native stderr text such as
# "Cloning into..." to a terminating PowerShell error when 2>&1 is used while
# ErrorActionPreference is Stop. Replace the module-private Git runner in the
# module scope so Git success is decided only from its real process exit code.
& $module {
    function Invoke-JulesGit {
        param(
            [Parameter(Mandatory = $true)][string]$Git,
            [Parameter(Mandatory = $true)][string[]]$Arguments,
            [Parameter(Mandatory = $true)][string]$WorkingDirectory,
            [switch]$AllowFailure
        )

        $previousPrompt = $env:GIT_TERMINAL_PROMPT
        $previousErrorActionPreference = $ErrorActionPreference
        $env:GIT_TERMINAL_PROMPT = "1"
        $exitCode = -1
        $output = ""

        try {
            Push-Location -LiteralPath $WorkingDirectory
            try {
                $ErrorActionPreference = "Continue"
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

        if (($exitCode -ne 0) -and (-not $AllowFailure)) {
            $displayArguments = $Arguments -join " "
            throw "git $displayArguments failed with exit code $exitCode.`n$output"
        }

        return [pscustomobject]@{
            ExitCode = $exitCode
            Output = $output
        }
    }
}

$parameters = @{
    SummaryPath = $SummaryPath
    DryRun = $DryRun
}

if (-not [string]::IsNullOrWhiteSpace($ProjectId)) {
    $parameters.ProjectId = $ProjectId
}
if (-not [string]::IsNullOrWhiteSpace($JobId)) {
    $parameters.JobId = $JobId
}
if (-not [string]::IsNullOrWhiteSpace($ConfigPath)) {
    $parameters.ConfigPath = $ConfigPath
}

$result = Send-AntmuxSummary @parameters
$result | Format-List
