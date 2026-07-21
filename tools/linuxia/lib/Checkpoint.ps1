Set-StrictMode -Version 2.0

function Get-LinuxIACheckpointContractLibraryPaths {
    param([string]$RepoRoot)
    $lib=Join-Path $RepoRoot 'skills/state.checkpoint.v1/tools/lib'
    $paths=@()
    foreach($name in @('Common.ps1','InputContract.ps1','OutputContract.ps1')){
        $path=Join-Path $lib $name
        if(-not (Test-Path -LiteralPath $path -PathType Leaf)){throw "CLI_CHECKPOINT_CONTRACT_MISSING: $path"}
        $paths+=@($path)
    }
    return $paths
}

function New-LinuxIACheckpointId {
    param([string]$RunId,[int]$Sequence)
    $suffix=$RunId
    if($suffix.StartsWith('RUN-')){$suffix=$suffix.Substring(4)}
    return 'CHK-' + $suffix + '-' + $Sequence.ToString('0000')
}

function New-LinuxIACheckpointInput {
    param(
        [string]$TaskId,
        [string]$RunId,
        [string]$CorrelationId,
        [int]$Sequence,
        [AllowNull()]$ParentCheckpointId,
        [string]$TaskState,
        [string]$Phase,
        [string]$TargetPath,
        [AllowNull()]$Source,
        [string]$DecisionArtifact,
        [string]$IntentSha256,
        [string]$ActionSha256,
        [string]$DecisionSha256
    )
    $payload=[pscustomobject]@{
        phase=$Phase
        command='inspect'
        target_path=$TargetPath
        decision_artifact=$DecisionArtifact
        intent_sha256=$IntentSha256
        action_sha256=$ActionSha256
        decision_sha256=$DecisionSha256
    }
    $inputs=@()
    if($null -ne $Source){
        $artifactSuffix=$RunId
        if($artifactSuffix.StartsWith('RUN-')){$artifactSuffix=$artifactSuffix.Substring(4)}
        $inputs=@([pscustomobject]@{
            artifact_id=('ART-SOURCE-' + $artifactSuffix)
            path=[string]$Source.path
            sha256=[string]$Source.sha256
            bermuda_state='RAW'
        })
    }
    $seed=[pscustomobject]@{
        task_id=$TaskId
        run_id=$RunId
        sequence=$Sequence
        parent_checkpoint_id=$ParentCheckpointId
        task_state=$TaskState
        phase=$Phase
        target_path=$TargetPath
        source_sha256=if($null -eq $Source){$null}else{[string]$Source.sha256}
        decision_sha256=$DecisionSha256
    }
    return [pscustomobject]@{
        schema_version='state-checkpoint-input-v1'
        operation='CREATE'
        task_id=$TaskId
        run_id=$RunId
        correlation_id=$CorrelationId
        agent_id='linuxia-cli-01'
        idempotency_key=(Get-LinuxIAObjectSha256 $seed)
        task_state=$TaskState
        branch_id='BRANCH-CLI-MAIN'
        sequence=$Sequence
        attempt=1
        expected_parent_checkpoint_id=$ParentCheckpointId
        payload=$payload
        inputs=$inputs
        outputs=@()
    }
}

function New-LinuxIACheckpointOutput {
    param([string]$RepoRoot,$Input,[string]$Phase,[string]$CreatedAtUtc)
    foreach($contractLibrary in @(Get-LinuxIACheckpointContractLibraryPaths $RepoRoot)){. $contractLibrary}
    if(-not (Test-InputContract $Input)){throw 'CLI_CHECKPOINT_INPUT_INVALID: generated checkpoint input failed its contract'}
    $checkpointId=New-LinuxIACheckpointId ([string]$Input.run_id) ([int]$Input.sequence)
    $zero='sha256:' + ('0'*64)
    $result=[pscustomobject]@{
        checkpoint_id=$checkpointId
        checkpoint_status='COMMITTED'
        task_state=[string]$Input.task_state
        branch_id=[string]$Input.branch_id
        sequence=[int]$Input.sequence
        parent_checkpoint_id=$Input.expected_parent_checkpoint_id
        payload_sha256=(Get-LinuxIAObjectSha256 $Input.payload)
        checkpoint_sha256=$zero
        idempotency_key=[string]$Input.idempotency_key
        phase=$Phase
        created_at_utc=$CreatedAtUtc
        payload=$Input.payload
        inputs=@($Input.inputs)
        outputs=@($Input.outputs)
    }
    $result.checkpoint_sha256=Get-LinuxIAObjectSha256 $result 'checkpoint_sha256'
    $output=[pscustomobject]@{
        schema_version='state-checkpoint-output-v1'
        ok=$true
        operation='CREATE'
        result_state='COMMITTED'
        task_id=[string]$Input.task_id
        run_id=[string]$Input.run_id
        correlation_id=[string]$Input.correlation_id
        result=$result
        error=$null
    }
    if(-not (Test-OutputContract $output)){throw 'CLI_CHECKPOINT_OUTPUT_INVALID: generated checkpoint output failed its contract'}
    return $output
}

function Save-LinuxIACheckpoint {
    param([string]$RepoRoot,$Output,[bool]$Audit=$true)
    $checkpointId=[string]$Output.result.checkpoint_id
    $runId=[string]$Output.run_id
    $checkpointRel='state/checkpoints/' + $runId + '/' + $checkpointId + '.json'
    $eventRel='state/events/checkpoints.jsonl'
    if($Audit){
        $checkpointPath=Join-Path $RepoRoot $checkpointRel.Replace('/','\')
        if(Test-Path -LiteralPath $checkpointPath -PathType Leaf){
            $existing=Get-Content -LiteralPath $checkpointPath -Raw -Encoding UTF8 | ConvertFrom-Json
            if((ConvertTo-LinuxIACanonicalJson $existing) -ne (ConvertTo-LinuxIACanonicalJson $Output)){
                throw "CLI_CHECKPOINT_COLLISION: immutable checkpoint already exists with different content: $checkpointRel"
            }
        }else{
            Write-LinuxIAImmutableJson $checkpointPath $Output
            $event=[pscustomobject]@{
                schema_version='state-checkpoint-event-v1'
                event_id=('EVENT-' + $checkpointId.Substring(4))
                timestamp_utc=[DateTimeOffset]::UtcNow.ToString('o')
                task_id=[string]$Output.task_id
                run_id=$runId
                correlation_id=[string]$Output.correlation_id
                checkpoint_id=$checkpointId
                parent_checkpoint_id=$Output.result.parent_checkpoint_id
                sequence=[int]$Output.result.sequence
                phase=[string]$Output.result.phase
                checkpoint_sha256=[string]$Output.result.checkpoint_sha256
                checkpoint_artifact=$checkpointRel
            }
            Add-LinuxIAAuditEvent (Join-Path $RepoRoot $eventRel.Replace('/','\')) $event
        }
    }
    return [pscustomobject]@{
        checkpoint_id=$checkpointId
        task_state=[string]$Output.result.task_state
        sequence=[int]$Output.result.sequence
        parent_checkpoint_id=$Output.result.parent_checkpoint_id
        checkpoint_sha256=[string]$Output.result.checkpoint_sha256
        artifact=if($Audit){$checkpointRel}else{$null}
        event_log=if($Audit){$eventRel}else{$null}
    }
}
