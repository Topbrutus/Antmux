Set-StrictMode -Version 2.0

function New-OutputFixture {
    param([string]$Case)
    $sha='sha256:' + ('a' * 64)
    $validJson = @"
{"schema_version":"state-checkpoint-output-v1","ok":true,"operation":"CREATE","result_state":"COMMITTED","task_id":"TASK-0042","run_id":"RUN-20260720-0042","correlation_id":"CORR-20260720-0042-001","result":{"checkpoint_id":"CHK-TASK-0042-RUN-20260720-0042-0001","checkpoint_status":"COMMITTED","task_state":"RUNNING","branch_id":"BRANCH-MAIN","sequence":1,"parent_checkpoint_id":null,"payload_sha256":"$sha","checkpoint_sha256":"$sha","inputs":[],"outputs":[]},"error":null}
"@
    $valid = $validJson | ConvertFrom-Json
    switch ($Case) {
        'valid_create_output' { return $valid }
        'raw_array_output' { return ,@() }
        'missing_result' { $valid.result=$null;return $valid }
        'wrong_result_state' { $valid.result_state='VERIFIED';return $valid }
        'valid_rejection' {
            $json = @"
{"schema_version":"state-checkpoint-output-v1","ok":false,"operation":"CREATE","result_state":"REJECTED","task_id":"TASK-0042","run_id":"RUN-20260720-0042","correlation_id":"CORR-20260720-0042-001","result":null,"error":{"code":"PARENT_REQUIRED","reason":"Parent absent"}}
"@
            return ($json | ConvertFrom-Json)
        }
        default { throw "Unknown output fixture: $Case" }
    }
}

function Test-OutputContract {
    param($o)
    if ($null -eq $o -or $o -is [System.Array] -or -not ($o -is [pscustomobject])) { return $false }
    foreach ($n in @('schema_version','ok','operation','result_state','task_id','run_id','correlation_id')) { if (-not (Test-HasProperty $o $n)) { return $false } }
    if ([string]$o.schema_version -ne 'state-checkpoint-output-v1' -or -not ($o.ok -is [bool])) { return $false }
    $map=@{CREATE='COMMITTED';VERIFY='VERIFIED';LIST='LISTED';READ='READ';FORK='FORKED';RESTORE_PLAN='RESTORE_PLANNED';ACTIVATE_BRANCH='BRANCH_ACTIVATED';REBUILD_AUDIT_PROJECTION='AUDIT_REBUILT'}
    $operation=[string]$o.operation
    if (-not $map.ContainsKey($operation)) { return $false }
    if (-not (Test-Id ([string]$o.task_id) '^TASK-[A-Z0-9-]{1,64}$')) { return $false }
    if (-not (Test-Id ([string]$o.run_id) '^RUN-[A-Z0-9-]{1,80}$')) { return $false }
    if (-not (Test-Id ([string]$o.correlation_id) '^CORR-[A-Z0-9-]{1,96}$')) { return $false }
    if (Test-ContainsSecretField $o) { return $false }
    if ([bool]$o.ok) {
        $expectedState=[string]$map[$operation]
        if ([string]$o.result_state -ne $expectedState -or $null -eq $o.result) { return $false }
        if ($operation -eq 'CREATE') {
            foreach ($n in @('checkpoint_id','checkpoint_status','task_state','branch_id','sequence','parent_checkpoint_id','payload_sha256','checkpoint_sha256','inputs','outputs')) { if (-not (Test-HasProperty $o.result $n)) { return $false } }
            if (-not (Test-Id ([string]$o.result.checkpoint_id) '^CHK-[A-Z0-9-]{3,160}$')) { return $false }
            if ([int]$o.result.sequence -lt 1) { return $false }
            if ([int]$o.result.sequence -eq 1 -and $null -ne $o.result.parent_checkpoint_id) { return $false }
            if (-not (Test-Sha256 ([string]$o.result.payload_sha256)) -or -not (Test-Sha256 ([string]$o.result.checkpoint_sha256))) { return $false }
            if (-not (Test-ArtifactArray $o.result.inputs) -or -not (Test-ArtifactArray $o.result.outputs)) { return $false }
        }
    } else {
        if (@('REJECTED','FAILED') -notcontains [string]$o.result_state) { return $false }
        if (-not (Test-HasProperty $o 'error') -or $null -eq $o.error) { return $false }
        if (-not (Test-HasProperty $o.error 'code') -or -not (Test-HasProperty $o.error 'reason')) { return $false }
        if ([string]::IsNullOrWhiteSpace([string]$o.error.code) -or [string]::IsNullOrWhiteSpace([string]$o.error.reason)) { return $false }
    }
    return $true
}
