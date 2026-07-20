Set-StrictMode -Version 2.0

function New-InputFixture {
    param([string]$Case)
    $sha = 'sha256:' + ('a' * 64)
    $baseJson = @"
{"schema_version":"state-checkpoint-input-v1","operation":"CREATE","task_id":"TASK-0042","run_id":"RUN-20260720-0042","correlation_id":"CORR-20260720-0042-001","agent_id":"orchestrator-01","idempotency_key":"$sha","task_state":"RUNNING","branch_id":"BRANCH-MAIN","sequence":1,"attempt":1,"expected_parent_checkpoint_id":null,"payload":{"next_action":"review"},"inputs":[{"artifact_id":"ART-INPUT-001","path":"artifacts/input/source.md","sha256":"$sha","bermuda_state":"VALIDATED"}],"outputs":[]}
"@
    $base = $baseJson | ConvertFrom-Json
    switch ($Case) {
        'valid_root' { return $base }
        'valid_child' { $base.sequence=2;$base.expected_parent_checkpoint_id='CHK-TASK-0042-RUN-20260720-0042-0001';return $base }
        'missing_task_id' { $base.PSObject.Properties.Remove('task_id');return $base }
        'uppercase_sha' { $base.idempotency_key='sha256:' + ('A' * 64);return $base }
        'path_traversal' { $base.inputs[0].path='../secrets/key';return $base }
        'child_without_parent' { $base.sequence=2;return $base }
        'zero_sequence' { $base.sequence=0;return $base }
        'duplicate_artifact' { $base.inputs=@($base.inputs[0],$base.inputs[0]);return $base }
        'unknown_bermuda' { $base.inputs[0].bermuda_state='MAGIC';return $base }
        'secret_field' { $base.payload | Add-Member -NotePropertyName api_key -NotePropertyValue secret;return $base }
        'valid_fork' {
            $json = @"
{"schema_version":"state-checkpoint-input-v1","operation":"FORK","task_id":"TASK-0042","run_id":"RUN-20260720-0042","correlation_id":"CORR-20260720-0042-001","agent_id":"orchestrator-01","idempotency_key":"$sha","source_checkpoint_id":"CHK-TASK-0042-RUN-20260720-0042-0004","source_branch_id":"BRANCH-MAIN","new_branch_id":"BRANCH-ALT"}
"@
            return ($json | ConvertFrom-Json)
        }
        'same_branch_fork' { $x=New-InputFixture 'valid_fork';$x.new_branch_id='BRANCH-MAIN';return $x }
        'valid_restore_plan' {
            $json = @"
{"schema_version":"state-checkpoint-input-v1","operation":"RESTORE_PLAN","task_id":"TASK-0042","run_id":"RUN-20260720-0042","correlation_id":"CORR-20260720-0042-001","agent_id":"orchestrator-01","idempotency_key":"$sha","source_checkpoint_id":"CHK-TASK-0042-RUN-20260720-0042-0004","reason":"Reprendre avant erreur"}
"@
            return ($json | ConvertFrom-Json)
        }
        'activate_without_approval' {
            $json = @"
{"schema_version":"state-checkpoint-input-v1","operation":"ACTIVATE_BRANCH","task_id":"TASK-0042","run_id":"RUN-20260720-0042","correlation_id":"CORR-20260720-0042-001","agent_id":"orchestrator-01","idempotency_key":"$sha","branch_id":"BRANCH-ALT","current_task_state":"RUNNING","approval_ref":null}
"@
            return ($json | ConvertFrom-Json)
        }
        'activate_with_approval' { $x=New-InputFixture 'activate_without_approval';$x.approval_ref='APPROVAL-BRUTUS-001';return $x }
        default { throw "Unknown input fixture: $Case" }
    }
}

function Test-InputContract {
    param($o)
    if ($null -eq $o -or $o -is [System.Array] -or -not ($o -is [pscustomobject])) { return $false }
    foreach ($n in @('schema_version','operation','task_id','run_id','correlation_id','agent_id','idempotency_key')) { if (-not (Test-HasProperty $o $n)) { return $false } }
    if ([string]$o.schema_version -ne 'state-checkpoint-input-v1') { return $false }
    $ops=@('CREATE','VERIFY','LIST','READ','FORK','RESTORE_PLAN','ACTIVATE_BRANCH','REBUILD_AUDIT_PROJECTION')
    if ($ops -notcontains [string]$o.operation) { return $false }
    if (-not (Test-Id ([string]$o.task_id) '^TASK-[A-Z0-9-]{1,64}$')) { return $false }
    if (-not (Test-Id ([string]$o.run_id) '^RUN-[A-Z0-9-]{1,80}$')) { return $false }
    if (-not (Test-Id ([string]$o.correlation_id) '^CORR-[A-Z0-9-]{1,96}$')) { return $false }
    if (-not (Test-Id ([string]$o.agent_id) '^[a-z0-9][a-z0-9._-]{1,63}$')) { return $false }
    if (-not (Test-Sha256 ([string]$o.idempotency_key)) -or (Test-ContainsSecretField $o)) { return $false }
    if ((Test-HasProperty $o 'inputs') -and -not (Test-ArtifactArray $o.inputs)) { return $false }
    if ((Test-HasProperty $o 'outputs') -and -not (Test-ArtifactArray $o.outputs)) { return $false }

    switch ([string]$o.operation) {
        'CREATE' {
            foreach ($n in @('task_state','branch_id','sequence','payload','expected_parent_checkpoint_id')) { if (-not (Test-HasProperty $o $n)) { return $false } }
            if (@('DISCOVERED','SELECTED','LOADED','AUTHORIZED','RUNNING','UNDER_REVIEW','VALIDATED','REJECTED','FAILED','ROLLED_BACK') -notcontains [string]$o.task_state) { return $false }
            if (-not (Test-Id ([string]$o.branch_id) '^BRANCH-[A-Z0-9-]{1,80}$')) { return $false }
            if ([int]$o.sequence -lt 1) { return $false }
            if ([int]$o.sequence -eq 1 -and $null -ne $o.expected_parent_checkpoint_id) { return $false }
            if ([int]$o.sequence -gt 1) {
                if ($null -eq $o.expected_parent_checkpoint_id) { return $false }
                if (-not (Test-Id ([string]$o.expected_parent_checkpoint_id) '^CHK-[A-Z0-9-]{3,160}$')) { return $false }
            }
        }
        'FORK' {
            foreach ($n in @('source_checkpoint_id','source_branch_id','new_branch_id')) { if (-not (Test-HasProperty $o $n)) { return $false } }
            if (-not (Test-Id ([string]$o.source_checkpoint_id) '^CHK-[A-Z0-9-]{3,160}$')) { return $false }
            if (-not (Test-Id ([string]$o.source_branch_id) '^BRANCH-[A-Z0-9-]{1,80}$')) { return $false }
            if (-not (Test-Id ([string]$o.new_branch_id) '^BRANCH-[A-Z0-9-]{1,80}$')) { return $false }
            if ([string]$o.source_branch_id -eq [string]$o.new_branch_id) { return $false }
        }
        'RESTORE_PLAN' {
            if (-not (Test-HasProperty $o 'source_checkpoint_id') -or -not (Test-HasProperty $o 'reason')) { return $false }
            if (-not (Test-Id ([string]$o.source_checkpoint_id) '^CHK-[A-Z0-9-]{3,160}$')) { return $false }
            if ([string]::IsNullOrWhiteSpace([string]$o.reason)) { return $false }
        }
        'ACTIVATE_BRANCH' {
            foreach ($n in @('branch_id','current_task_state','approval_ref')) { if (-not (Test-HasProperty $o $n)) { return $false } }
            if (-not (Test-Id ([string]$o.branch_id) '^BRANCH-[A-Z0-9-]{1,80}$')) { return $false }
            if (@('RUNNING','UNDER_REVIEW','VALIDATED','REJECTED','FAILED','ROLLED_BACK') -contains [string]$o.current_task_state) {
                if ($null -eq $o.approval_ref -or -not (Test-Id ([string]$o.approval_ref) '^APPROVAL-[A-Z0-9-]{1,96}$')) { return $false }
            }
        }
    }
    return $true
}
