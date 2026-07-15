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
Import-Module -Name $modulePath -Force

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
