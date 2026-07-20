Set-StrictMode -Version 2.0

function New-OutputFixture {
    param([string]$Case)
    $shaA='sha256:' + ('a' * 64)
    $shaB='sha256:' + ('b' * 64)
    $shaC='sha256:' + ('c' * 64)
    $shaD='sha256:' + ('d' * 64)
    $shaE='sha256:' + ('e' * 64)
    $json=@"
{
  "schema_version":"intent-authorization-output-v1",
  "decision_id":"DECISION-TASK-0042-017",
  "task_id":"TASK-0042",
  "run_id":"RUN-20260720-0042",
  "correlation_id":"CORR-20260720-0042-017",
  "decision":"ALLOW",
  "reason_codes":["ALL_CONSTRAINTS_SATISFIED"],
  "matched_constraints":["tool_name","operation","resource_scope","rent_budget"],
  "violated_constraints":[],
  "required_approvals":[],
  "intent_sha256":"$shaA",
  "action_sha256":"$shaB",
  "permission_snapshot_sha256":"$shaC",
  "policy_sha256":"$shaD",
  "decision_payload_sha256":"$shaE",
  "evaluated_at_utc":"2026-07-20T22:01:00Z",
  "expires_at_utc":"2026-07-20T22:06:00Z"
}
"@
    $o=$json | ConvertFrom-Json
    switch ($Case) {
        'valid_allow' { return $o }
        'valid_deny' { $o.decision='DENY';$o.reason_codes=@('STATIC_PERMISSION_DENIED');$o.matched_constraints=@();$o.violated_constraints=@('tool_name');return $o }
        'valid_require_approval' { $o.decision='REQUIRE_HUMAN_APPROVAL';$o.reason_codes=@('APPROVAL_REQUIRED');$o.required_approvals=@('ACTION-TASK-0042-017');return $o }
        'raw_array' { return @($o,$o) }
        'missing_decision' { $o.PSObject.Properties.Remove('decision');return $o }
        'allow_with_violations' { $o.violated_constraints=@('tool_name');return $o }
        'deny_without_reason' { $o.decision='DENY';$o.reason_codes=@();return $o }
        'approval_without_required' { $o.decision='REQUIRE_HUMAN_APPROVAL';$o.reason_codes=@('APPROVAL_REQUIRED');$o.required_approvals=@();return $o }
        'uppercase_hash' { $o.action_sha256='sha256:' + ('B' * 64);return $o }
        default { throw "Unknown output fixture: $Case" }
    }
}

function Test-AuthorizationOutput {
    param($o)
    if ($null -eq $o -or $o -is [System.Array] -or -not ($o -is [pscustomobject])) { return $false }
    foreach ($n in @('schema_version','decision_id','task_id','run_id','correlation_id','decision','reason_codes','matched_constraints','violated_constraints','required_approvals','intent_sha256','action_sha256','permission_snapshot_sha256','policy_sha256','decision_payload_sha256','evaluated_at_utc','expires_at_utc')) {
        if (-not (Test-HasProperty $o $n)) { return $false }
    }
    if ([string]$o.schema_version -ne 'intent-authorization-output-v1') { return $false }
    if (-not (Test-Id ([string]$o.decision_id) '^DECISION-[A-Z0-9-]{1,128}$')) { return $false }
    if (-not (Test-Id ([string]$o.task_id) '^TASK-[A-Z0-9-]{1,64}$')) { return $false }
    if (-not (Test-Id ([string]$o.run_id) '^RUN-[A-Z0-9-]{1,80}$')) { return $false }
    if (-not (Test-Id ([string]$o.correlation_id) '^CORR-[A-Z0-9-]{1,96}$')) { return $false }
    if (@('ALLOW','DENY','REQUIRE_HUMAN_APPROVAL') -notcontains [string]$o.decision) { return $false }
    if (@($o.reason_codes).Count -lt 1) { return $false }
    foreach ($h in @('intent_sha256','action_sha256','permission_snapshot_sha256','policy_sha256','decision_payload_sha256')) {
        if (-not (Test-Sha256 ([string]$o.$h))) { return $false }
    }
    if (-not (Test-UtcDate ([string]$o.evaluated_at_utc)) -or -not (Test-UtcDate ([string]$o.expires_at_utc))) { return $false }
    if ((Get-UtcDate ([string]$o.expires_at_utc)) -lt (Get-UtcDate ([string]$o.evaluated_at_utc))) { return $false }
    if ([string]$o.decision -eq 'ALLOW') {
        if (@($o.violated_constraints).Count -ne 0 -or @($o.required_approvals).Count -ne 0) { return $false }
    }
    if ([string]$o.decision -eq 'REQUIRE_HUMAN_APPROVAL' -and @($o.required_approvals).Count -eq 0) { return $false }
    if (Test-ContainsSecretField $o) { return $false }
    return $true
}
