Set-StrictMode -Version 2.0

function Add-LinuxIATestResult {
    param([string]$Id,[bool]$Passed,[string]$Description)
    $null=$script:Results.Add([pscustomobject]@{id=$Id;passed=$Passed;description=$Description})
    $prefix=if($Passed){'[PASS]'}else{'[FAIL]'}
    Write-Host "$prefix $Id - $Description"
}

function Get-LinuxIARepoRoot {
    param([string]$CliRoot)
    return (Resolve-Path -LiteralPath (Join-Path $CliRoot '../..')).Path
}

function New-LinuxIAExecutionIds {
    $stamp=[DateTimeOffset]::UtcNow.ToString('yyyyMMddHHmmssfff')
    return [pscustomobject]@{
        task_id="TASK-CLI-$stamp"
        run_id="RUN-CLI-$stamp"
        correlation_id="CORR-CLI-$stamp-001"
        intent_id="INTENT-CLI-$stamp-001"
        action_id="ACTION-CLI-$stamp-001"
        decision_id="DECISION-CLI-$stamp-001"
        event_id="EVENT-CLI-$stamp-001"
    }
}

function Get-LinuxIAFileSha256 {
    param([string]$Path)
    return 'sha256:' + (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-LinuxIAErrorCode {
    param([System.Management.Automation.ErrorRecord]$ErrorRecord)
    $message=[string]$ErrorRecord.Exception.Message
    if($message -match '^([A-Z0-9_]+):'){return $Matches[1]}
    return 'CLI_INTERNAL_ERROR'
}
