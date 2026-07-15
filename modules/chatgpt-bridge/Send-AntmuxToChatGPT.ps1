#requires -Version 5.1

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SummaryPath,
    [string]$ConfigPath,
    [switch]$TestOnly,
    [switch]$NoEnter,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$modulePath = Join-Path $PSScriptRoot "ChatGPT.Bridge.psm1"
Import-Module -Name $modulePath -Force

$parameters = @{
    SummaryPath = $SummaryPath
    TestOnly = $TestOnly
    NoEnter = $NoEnter
    Force = $Force
}
if (-not [string]::IsNullOrWhiteSpace($ConfigPath)) {
    $parameters.ConfigPath = $ConfigPath
}

$result = Send-AntmuxToChatGPT @parameters
$result | Format-List
