[CmdletBinding()]
param(
    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$SkillRoot = (Split-Path -Parent $PSScriptRoot),

    [Parameter()]
    [switch]$Quiet,

    [Parameter()]
    [switch]$PassThru
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:Results = New-Object System.Collections.ArrayList

foreach ($library in @(
    'lib/Yaml.ps1',
    'lib/ContractCommon.ps1',
    'lib/InputContract.ps1',
    'lib/OutputContract.ps1',
    'lib/Permissions.ps1',
    'lib/Integrity.ps1',
    'lib/PackageChecks.ps1',
    'lib/PermissionChecks.ps1',
    'lib/ContractChecks.ps1'
)) {
    . (Join-Path $PSScriptRoot $library)
}

function Add-ValidationResult {
    param(
        [Parameter(Mandatory = $true)][string]$Id,
        [Parameter(Mandatory = $true)][bool]$Passed,
        [Parameter(Mandatory = $true)][string]$Message,
        [string]$Details = ''
    )

    $status = if ($Passed) { 'PASS' } else { 'FAIL' }
    [void]$script:Results.Add([pscustomobject]@{
        id = $Id
        status = $status
        message = $Message
        details = $Details
    })

    if (-not $Quiet) {
        $prefix = if ($Passed) { '[PASS]' } else { '[FAIL]' }
        if ([string]::IsNullOrWhiteSpace($Details)) {
            Write-Host "$prefix $Id - $Message"
        }
        else {
            Write-Host "$prefix $Id - $Message :: $Details"
        }
    }
}

try {
    $resolvedSkillRoot = (Resolve-Path -LiteralPath $SkillRoot).Path

    if (-not $Quiet) {
        Write-Host 'ANTMUX AGENT SKILL VALIDATOR'
        Write-Host "SKILL_ROOT: $resolvedSkillRoot"
        Write-Host 'MODE: READ_ONLY'
        Write-Host ''
    }

    Add-ValidationResult -Id 'ENV-001' `
        -Passed ($PSVersionTable.PSVersion.Major -eq 5 -and $PSVersionTable.PSVersion.Minor -ge 1) `
        -Message 'PowerShell 5.1 compatibility' `
        -Details ([string]$PSVersionTable.PSVersion)

    $state = Invoke-PackageChecks -Root $resolvedSkillRoot
    Invoke-PermissionChecks -Manifest $state.manifest -PermissionSuite $state.permission_suite
    Invoke-ContractChecks -Root $resolvedSkillRoot -ContractSuite $state.contract_suite

    $failed = @($script:Results | Where-Object { $_.status -ceq 'FAIL' })
    $passed = @($script:Results | Where-Object { $_.status -ceq 'PASS' })

    if (-not $Quiet) {
        Write-Host ''
        Write-Host "TOTAL: $($script:Results.Count)"
        Write-Host "PASSED: $($passed.Count)"
        Write-Host "FAILED: $($failed.Count)"
        if ($failed.Count -eq 0) {
            Write-Host 'ALL_TESTS: PASS'
        }
        else {
            Write-Host 'ALL_TESTS: FAIL'
        }
    }

    $summary = [pscustomobject]@{
        skill_root = $resolvedSkillRoot
        mode = 'READ_ONLY'
        total = $script:Results.Count
        passed = $passed.Count
        failed = $failed.Count
        result = if ($failed.Count -eq 0) { 'ALL_TESTS: PASS' } else { 'ALL_TESTS: FAIL' }
        results = @($script:Results)
    }

    if ($PassThru) {
        Write-Output $summary
    }

    if ($failed.Count -gt 0) {
        exit 1
    }
    exit 0
}
catch {
    if (-not $Quiet) {
        Write-Host '[FATAL] VALIDATOR_EXCEPTION'
        Write-Host $_.Exception.Message
        Write-Host 'ALL_TESTS: FAIL'
    }

    if ($PassThru) {
        Write-Output ([pscustomobject]@{
            skill_root = $SkillRoot
            mode = 'READ_ONLY'
            total = $script:Results.Count
            passed = @($script:Results | Where-Object { $_.status -ceq 'PASS' }).Count
            failed = @($script:Results | Where-Object { $_.status -ceq 'FAIL' }).Count + 1
            result = 'ALL_TESTS: FAIL'
            fatal_error = $_.Exception.Message
            results = @($script:Results)
        })
    }
    exit 2
}
