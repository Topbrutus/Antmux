Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$cliRoot=$PSScriptRoot
. (Join-Path $cliRoot 'lib/Common.ps1')
. (Join-Path $cliRoot 'lib/CanonicalJson.ps1')
. (Join-Path $cliRoot 'lib/PathPolicy.ps1')
. (Join-Path $cliRoot 'lib/Audit.ps1')
. (Join-Path $cliRoot 'lib/Checkpoint.ps1')
. (Join-Path $cliRoot 'Invoke-Inspect.ps1')

function Show-LinuxIAUsage {
    Write-Host 'LinuxIA CLI PowerShell v0.1'
    Write-Host 'Usage: .\tools\linuxia.ps1 inspect --file <relative-path> [--json]'
}

try{
    $all=@($args)
    if($all.Count -eq 0 -or @('help','--help','-h') -contains [string]$all[0]){Show-LinuxIAUsage;exit 0}
    $command=([string]$all[0]).ToLowerInvariant()
    if($command -ne 'inspect'){throw "CLI_UNKNOWN_COMMAND: $command"}
    $parsed=ConvertFrom-LinuxIAInspectArguments @($all | Select-Object -Skip 1)
    $repoRoot=Get-LinuxIARepoRoot $cliRoot
    $result=Invoke-LinuxIAInspect $repoRoot $parsed.file $true
    if($parsed.json){Write-Output (ConvertTo-LinuxIACanonicalJson $result)}else{
        Write-Host 'LINUXIA CLI v0.1'
        Write-Host 'COMMAND: inspect'
        Write-Host ('STATUS: ' + $result.status)
        Write-Host ('DECISION: ' + $result.decision)
        Write-Host ('REASON: ' + $result.reason)
        if($null -ne $result.source){
            Write-Host ('FILE: ' + $result.source.path)
            Write-Host ('BYTES: ' + $result.source.bytes)
            Write-Host ('SHA256: ' + $result.source.sha256)
        }
        if($null -ne $result.checkpoints){
            Write-Host ('PRE_CHECKPOINT: ' + $result.checkpoints.pre_action.checkpoint_id)
            Write-Host ('PRE_CHECKPOINT_ARTIFACT: ' + $result.checkpoints.pre_action.artifact)
            Write-Host ('POST_CHECKPOINT: ' + $result.checkpoints.post_action.checkpoint_id)
            Write-Host ('POST_CHECKPOINT_ARTIFACT: ' + $result.checkpoints.post_action.artifact)
            Write-Host ('CHECKPOINT_CHAIN_VALID: ' + $result.checkpoints.chain_valid)
            Write-Host ('CHECKPOINT_LOG: ' + $result.checkpoints.event_log)
        }
        Write-Host ('DECISION_ARTIFACT: ' + $result.decision_artifact)
        Write-Host ('AUDIT_LOG: ' + $result.audit_log)
    }
    if($result.decision -eq 'ALLOW'){exit 0}
    if($result.decision -eq 'REQUIRE_HUMAN_APPROVAL'){exit 3}
    exit 2
}catch{
    $code=Get-LinuxIAErrorCode $_
    Write-Error ($code + ': ' + $_.Exception.Message) -ErrorAction Continue
    exit 4
}
