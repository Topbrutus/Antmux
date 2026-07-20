Set-StrictMode -Version 2.0

function New-AuthorizationFixture {
    param([string]$Case)
    $shaA='sha256:' + ('a' * 64)
    $shaB='sha256:' + ('b' * 64)
    $shaC='sha256:' + ('c' * 64)
    $shaD='sha256:' + ('d' * 64)
    $json=@"
{
  "schema_version":"intent-authorization-input-v1",
  "task_id":"TASK-0042",
  "run_id":"RUN-20260720-0042",
  "correlation_id":"CORR-20260720-0042-017",
  "authorizer_id":"intent-authorizer-01",
  "intent_envelope":{
    "schema_version":"intent-envelope-v1",
    "intent_id":"INTENT-TASK-0042-001",
    "task_id":"TASK-0042",
    "confirmed_by_user":true,
    "objective":"Analyser la source et écrire seulement un rapport.",
    "allowed_actions":["READ","ANALYZE","WRITE_REPORT"],
    "denied_actions":["DELETE","PUBLISH","SEND_MESSAGE","OVERWRITE_SOURCE"],
    "allowed_tools":["source.read","report.write"],
    "resource_scopes":[
      {"mode":"read","pattern":"inputs/**"},
      {"mode":"write","pattern":"reports/**"}
    ],
    "network_allowed":false,
    "external_effects_allowed":false,
    "destructive_actions_allowed":false,
    "max_items":25,
    "rent_budget":{"max_tool_calls":20,"max_inference_ms":120000,"max_bytes_written":200000},
    "expires_at_utc":"2026-07-21T02:00:00Z",
    "intent_sha256":"$shaA"
  },
  "proposed_action":{
    "schema_version":"proposed-action-v1",
    "action_id":"ACTION-TASK-0042-017",
    "task_id":"TASK-0042",
    "run_id":"RUN-20260720-0042",
    "correlation_id":"CORR-20260720-0042-017",
    "agent_id":"worker-01",
    "skill_id":"reviewer.scientific",
    "skill_version":"1.0.0",
    "operation":"READ",
    "tool_name":"source.read",
    "arguments":{"path":"inputs/source.md","mode":"read","item_count":1},
    "estimated_rent":{"tool_calls":1,"inference_ms":0,"bytes_written":0},
    "external_effect":false,
    "destructive":false,
    "action_sha256":"$shaB"
  },
  "permission_snapshot":{
    "allowed_tools":["source.read","report.write"],
    "denied_tools":["github.push","filesystem.delete","network.request"],
    "filesystem_read":["inputs/**","artifacts/**"],
    "filesystem_write":["reports/**"],
    "network_allowed":false,
    "current_attempt":1,
    "max_attempts":2,
    "permission_snapshot_sha256":"$shaC"
  },
  "risk_policy":{
    "operations_requiring_approval":["WRITE_REPORT","PUBLISH","SEND_MESSAGE","INSTALL","ACTIVATE_MODEL"],
    "tools_requiring_approval":["github.push"],
    "destructive_requires_approval":true,
    "external_effect_requires_approval":true,
    "budget_excess_requires_approval":true,
    "policy_sha256":"$shaD"
  },
  "approval_refs":[],
  "current_rent":{"tool_calls":2,"inference_ms":1000,"bytes_written":1000},
  "evaluated_at_utc":"2026-07-20T22:01:00Z"
}
"@
    $o=$json | ConvertFrom-Json
    switch ($Case) {
        'valid_read' { return $o }
        'missing_task_id' { $o.PSObject.Properties.Remove('task_id');return $o }
        'uppercase_intent_sha' { $o.intent_envelope.intent_sha256='sha256:' + ('A' * 64);return $o }
        'task_mismatch' { $o.proposed_action.task_id='TASK-9999';return $o }
        'secret_field' { $o.proposed_action.arguments | Add-Member -NotePropertyName api_key -NotePropertyValue secret;return $o }
        'unsafe_scope' { $o.intent_envelope.resource_scopes[0].pattern='../inputs/**';return $o }
        'path_traversal' { $o.proposed_action.arguments.path='../secrets/token.txt';return $o }
        'invalid_approval_hash' {
            $o.approval_refs=@([pscustomobject]@{approval_id='APPROVAL-001';action_sha256='bad';intent_sha256=$shaA;valid_until_utc='2026-07-21T01:00:00Z';approved_by='Gabi'})
            return $o
        }
        'tool_static_missing' { $o.proposed_action.tool_name='unknown.tool';$o.intent_envelope.allowed_tools+=@('unknown.tool');return $o }
        'tool_static_denied' { $o.proposed_action.tool_name='github.push';$o.intent_envelope.allowed_tools+=@('github.push');return $o }
        'operation_denied' { $o.proposed_action.operation='DELETE';return $o }
        'operation_not_allowed' { $o.proposed_action.operation='ARCHIVE';return $o }
        'tool_not_in_intent' { $o.intent_envelope.allowed_tools=@('report.write');return $o }
        'path_outside_intent' { $o.proposed_action.arguments.path='artifacts/source.md';return $o }
        'path_outside_static' {
            $o.proposed_action.arguments.path='private/source.md'
            $o.intent_envelope.resource_scopes[0].pattern='private/**'
            return $o
        }
        'network_not_allowed' {
            $o.proposed_action.arguments | Add-Member -NotePropertyName network -NotePropertyValue $true
            return $o
        }
        'external_forbidden' { $o.proposed_action.external_effect=$true;return $o }
        'destructive_forbidden' { $o.proposed_action.destructive=$true;return $o }
        'expired_intent' { $o.intent_envelope.expires_at_utc='2026-07-20T21:00:00Z';return $o }
        'unconfirmed_intent' { $o.intent_envelope.confirmed_by_user=$false;return $o }
        'budget_exceeded' { $o.proposed_action.estimated_rent.tool_calls=19;return $o }
        'items_exceeded' { $o.proposed_action.arguments.item_count=26;return $o }
        'write_requires_approval' {
            $o.proposed_action.operation='WRITE_REPORT'
            $o.proposed_action.tool_name='report.write'
            $o.proposed_action.arguments.path='reports/review.md'
            $o.proposed_action.arguments.mode='write'
            $o.proposed_action.estimated_rent.bytes_written=12000
            return $o
        }
        'write_with_valid_approval' {
            $x=New-AuthorizationFixture 'write_requires_approval'
            $x.approval_refs=@([pscustomobject]@{approval_id='APPROVAL-GABI-001';action_sha256=$x.proposed_action.action_sha256;intent_sha256=$x.intent_envelope.intent_sha256;valid_until_utc='2026-07-21T01:00:00Z';approved_by='Gabi'})
            return $x
        }
        'approval_wrong_action' {
            $x=New-AuthorizationFixture 'write_requires_approval'
            $x.approval_refs=@([pscustomobject]@{approval_id='APPROVAL-GABI-001';action_sha256=('sha256:' + ('e' * 64));intent_sha256=$x.intent_envelope.intent_sha256;valid_until_utc='2026-07-21T01:00:00Z';approved_by='Gabi'})
            return $x
        }
        'approval_expired' {
            $x=New-AuthorizationFixture 'write_requires_approval'
            $x.approval_refs=@([pscustomobject]@{approval_id='APPROVAL-GABI-001';action_sha256=$x.proposed_action.action_sha256;intent_sha256=$x.intent_envelope.intent_sha256;valid_until_utc='2026-07-20T21:00:00Z';approved_by='Gabi'})
            return $x
        }
        'approval_cannot_override_static_deny' {
            $x=New-AuthorizationFixture 'tool_static_denied'
            $x.approval_refs=@([pscustomobject]@{approval_id='APPROVAL-GABI-001';action_sha256=$x.proposed_action.action_sha256;intent_sha256=$x.intent_envelope.intent_sha256;valid_until_utc='2026-07-21T01:00:00Z';approved_by='Gabi'})
            return $x
        }
        'attempt_exceeded' { $o.permission_snapshot.current_attempt=3;return $o }
        default { throw "Unknown authorization fixture: $Case" }
    }
}

function Test-AuthorizationInput {
    param($o)
    if ($null -eq $o -or $o -is [System.Array] -or -not ($o -is [pscustomobject])) { return $false }
    foreach ($n in @('schema_version','task_id','run_id','correlation_id','authorizer_id','intent_envelope','proposed_action','permission_snapshot','risk_policy','approval_refs','current_rent','evaluated_at_utc')) {
        if (-not (Test-HasProperty $o $n)) { return $false }
    }
    if ([string]$o.schema_version -ne 'intent-authorization-input-v1') { return $false }
    if (-not (Test-Id ([string]$o.task_id) '^TASK-[A-Z0-9-]{1,64}$')) { return $false }
    if (-not (Test-Id ([string]$o.run_id) '^RUN-[A-Z0-9-]{1,80}$')) { return $false }
    if (-not (Test-Id ([string]$o.correlation_id) '^CORR-[A-Z0-9-]{1,96}$')) { return $false }
    if (-not (Test-Id ([string]$o.authorizer_id) '^[a-z0-9][a-z0-9._-]{1,63}$')) { return $false }
    if (-not (Test-UtcDate ([string]$o.evaluated_at_utc)) -or (Test-ContainsSecretField $o)) { return $false }

    $i=$o.intent_envelope
    foreach ($n in @('schema_version','intent_id','task_id','confirmed_by_user','objective','allowed_actions','denied_actions','allowed_tools','resource_scopes','network_allowed','external_effects_allowed','destructive_actions_allowed','max_items','rent_budget','expires_at_utc','intent_sha256')) {
        if (-not (Test-HasProperty $i $n)) { return $false }
    }
    if ([string]$i.schema_version -ne 'intent-envelope-v1') { return $false }
    if (-not (Test-Id ([string]$i.intent_id) '^INTENT-[A-Z0-9-]{1,128}$')) { return $false }
    if ([string]$i.task_id -ne [string]$o.task_id) { return $false }
    if ([string]::IsNullOrWhiteSpace([string]$i.objective)) { return $false }
    if (-not (Test-StringArray $i.allowed_actions) -or -not (Test-StringArray $i.denied_actions) -or -not (Test-StringArray $i.allowed_tools)) { return $false }
    if (@($i.allowed_actions | Where-Object { $i.denied_actions -contains $_ }).Count -gt 0) { return $false }
    foreach ($s in @($i.resource_scopes)) {
        foreach ($n in @('mode','pattern')) { if (-not (Test-HasProperty $s $n)) { return $false } }
        if (@('read','write') -notcontains [string]$s.mode -or -not (Test-SafePath ([string]$s.pattern))) { return $false }
    }
    if ([int]$i.max_items -lt 1 -or -not (Test-UtcDate ([string]$i.expires_at_utc)) -or -not (Test-Sha256 ([string]$i.intent_sha256)) ) { return $false }
    foreach ($n in @('max_tool_calls','max_inference_ms','max_bytes_written')) {
        if (-not (Test-HasProperty $i.rent_budget $n) -or -not (Test-NonNegativeInteger $i.rent_budget.$n)) { return $false }
    }

    $a=$o.proposed_action
    foreach ($n in @('schema_version','action_id','task_id','run_id','correlation_id','agent_id','skill_id','skill_version','operation','tool_name','arguments','estimated_rent','external_effect','destructive','action_sha256')) {
        if (-not (Test-HasProperty $a $n)) { return $false }
    }
    if ([string]$a.schema_version -ne 'proposed-action-v1') { return $false }
    if ([string]$a.task_id -ne [string]$o.task_id -or [string]$a.run_id -ne [string]$o.run_id -or [string]$a.correlation_id -ne [string]$o.correlation_id) { return $false }
    if (-not (Test-Id ([string]$a.action_id) '^ACTION-[A-Z0-9-]{1,128}$')) { return $false }
    if (-not (Test-Id ([string]$a.agent_id) '^[a-z0-9][a-z0-9._-]{1,63}$')) { return $false }
    if (-not (Test-Id ([string]$a.skill_id) '^[a-z0-9][a-z0-9._-]{1,127}$')) { return $false }
    if (-not (Test-Id ([string]$a.skill_version) '^[0-9]+\.[0-9]+\.[0-9]+$')) { return $false }
    if (-not (Test-Id ([string]$a.operation) '^[A-Z][A-Z0-9_]{1,63}$')) { return $false }
    if (-not (Test-Id ([string]$a.tool_name) '^[a-z0-9][a-z0-9._-]{1,127}$')) { return $false }
    if ((Test-HasProperty $a.arguments 'path') -and -not (Test-SafePath ([string]$a.arguments.path))) { return $false }
    if (-not (Test-Sha256 ([string]$a.action_sha256))) { return $false }
    foreach ($n in @('tool_calls','inference_ms','bytes_written')) {
        if (-not (Test-HasProperty $a.estimated_rent $n) -or -not (Test-NonNegativeInteger $a.estimated_rent.$n)) { return $false }
    }

    $p=$o.permission_snapshot
    foreach ($n in @('allowed_tools','denied_tools','filesystem_read','filesystem_write','network_allowed','current_attempt','max_attempts','permission_snapshot_sha256')) {
        if (-not (Test-HasProperty $p $n)) { return $false }
    }
    if (-not (Test-Sha256 ([string]$p.permission_snapshot_sha256))) { return $false }
    if ([int]$p.current_attempt -lt 1 -or [int]$p.max_attempts -lt 1) { return $false }
    foreach ($scope in @($p.filesystem_read)+@($p.filesystem_write)) { if (-not (Test-SafePath ([string]$scope))) { return $false } }

    $r=$o.risk_policy
    foreach ($n in @('operations_requiring_approval','tools_requiring_approval','destructive_requires_approval','external_effect_requires_approval','budget_excess_requires_approval','policy_sha256')) {
        if (-not (Test-HasProperty $r $n)) { return $false }
    }
    if (-not (Test-Sha256 ([string]$r.policy_sha256))) { return $false }

    foreach ($approval in @($o.approval_refs)) {
        foreach ($n in @('approval_id','action_sha256','intent_sha256','valid_until_utc','approved_by')) { if (-not (Test-HasProperty $approval $n)) { return $false } }
        if (-not (Test-Id ([string]$approval.approval_id) '^APPROVAL-[A-Z0-9-]{1,128}$')) { return $false }
        if (-not (Test-Sha256 ([string]$approval.action_sha256)) -or -not (Test-Sha256 ([string]$approval.intent_sha256))) { return $false }
        if (-not (Test-UtcDate ([string]$approval.valid_until_utc)) -or [string]::IsNullOrWhiteSpace([string]$approval.approved_by)) { return $false }
    }

    foreach ($n in @('tool_calls','inference_ms','bytes_written')) {
        if (-not (Test-HasProperty $o.current_rent $n) -or -not (Test-NonNegativeInteger $o.current_rent.$n)) { return $false }
    }
    return $true
}
