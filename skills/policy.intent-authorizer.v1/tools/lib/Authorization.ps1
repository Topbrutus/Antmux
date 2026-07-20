Set-StrictMode -Version 2.0

function New-DecisionResult {
    param([string]$Decision,[string]$Reason)
    return [pscustomobject]@{decision=$Decision;reason=$Reason}
}

function Get-AuthorizationDecision {
    param($o)
    if (-not (Test-AuthorizationInput $o)) { return New-DecisionResult 'DENY' 'INPUT_INVALID' }

    $i=$o.intent_envelope
    $a=$o.proposed_action
    $p=$o.permission_snapshot
    $r=$o.risk_policy
    $evaluated=Get-UtcDate ([string]$o.evaluated_at_utc)

    if ((Get-UtcDate ([string]$i.expires_at_utc)) -lt $evaluated) { return New-DecisionResult 'DENY' 'INTENT_EXPIRED' }
    if ([int]$p.current_attempt -gt [int]$p.max_attempts) { return New-DecisionResult 'DENY' 'MAX_ATTEMPTS_EXCEEDED' }
    if (@($p.denied_tools) -contains [string]$a.tool_name) { return New-DecisionResult 'DENY' 'STATIC_PERMISSION_DENIED' }
    if (@($p.allowed_tools) -notcontains [string]$a.tool_name) { return New-DecisionResult 'DENY' 'STATIC_PERMISSION_MISSING' }

    $networkRequested=$false
    if (Test-HasProperty $a.arguments 'network') { $networkRequested=[bool]$a.arguments.network }
    if ($networkRequested -and (-not [bool]$p.network_allowed -or -not [bool]$i.network_allowed)) { return New-DecisionResult 'DENY' 'NETWORK_NOT_ALLOWED' }

    if (@($i.denied_actions) -contains [string]$a.operation) { return New-DecisionResult 'DENY' 'INTENT_OPERATION_DENIED' }
    if (@($i.allowed_actions) -notcontains [string]$a.operation) { return New-DecisionResult 'DENY' 'INTENT_OPERATION_NOT_ALLOWED' }
    if (@($i.allowed_tools) -notcontains [string]$a.tool_name) { return New-DecisionResult 'DENY' 'INTENT_TOOL_NOT_ALLOWED' }

    if (Test-HasProperty $a.arguments 'path') {
        $mode=if(Test-HasProperty $a.arguments 'mode'){[string]$a.arguments.mode}else{'read'}
        $path=[string]$a.arguments.path
        $intentPatterns=@($i.resource_scopes | Where-Object {[string]$_.mode -eq $mode} | ForEach-Object {[string]$_.pattern})
        if (-not (Test-PathMatches $path $intentPatterns)) { return New-DecisionResult 'DENY' 'INTENT_RESOURCE_SCOPE_MISMATCH' }
        $staticPatterns=if($mode -eq 'write'){@($p.filesystem_write)}else{@($p.filesystem_read)}
        if (-not (Test-PathMatches $path $staticPatterns)) { return New-DecisionResult 'DENY' 'STATIC_RESOURCE_SCOPE_MISMATCH' }
    }

    if ([bool]$a.external_effect -and -not [bool]$i.external_effects_allowed) { return New-DecisionResult 'DENY' 'INTENT_EXTERNAL_EFFECT_FORBIDDEN' }
    if ([bool]$a.destructive -and -not [bool]$i.destructive_actions_allowed) { return New-DecisionResult 'DENY' 'INTENT_DESTRUCTIVE_FORBIDDEN' }

    if (Test-HasProperty $a.arguments 'item_count') {
        if ([int64]$a.arguments.item_count -gt [int64]$i.max_items) { return New-DecisionResult 'REQUIRE_HUMAN_APPROVAL' 'MAX_ITEMS_EXCEEDED' }
    }

    $projectedToolCalls=[int64]$o.current_rent.tool_calls+[int64]$a.estimated_rent.tool_calls
    $projectedInference=[int64]$o.current_rent.inference_ms+[int64]$a.estimated_rent.inference_ms
    $projectedBytes=[int64]$o.current_rent.bytes_written+[int64]$a.estimated_rent.bytes_written
    if ($projectedToolCalls -gt [int64]$i.rent_budget.max_tool_calls -or $projectedInference -gt [int64]$i.rent_budget.max_inference_ms -or $projectedBytes -gt [int64]$i.rent_budget.max_bytes_written) {
        return New-DecisionResult 'REQUIRE_HUMAN_APPROVAL' 'RENT_BUDGET_EXCEEDED'
    }

    if (-not [bool]$i.confirmed_by_user) { return New-DecisionResult 'REQUIRE_HUMAN_APPROVAL' 'INTENT_CONFIRMATION_REQUIRED' }

    $approvalRequired=(@($r.operations_requiring_approval) -contains [string]$a.operation) -or
        (@($r.tools_requiring_approval) -contains [string]$a.tool_name) -or
        ([bool]$a.destructive -and [bool]$r.destructive_requires_approval) -or
        ([bool]$a.external_effect -and [bool]$r.external_effect_requires_approval)

    if ($approvalRequired) {
        if (@($o.approval_refs).Count -eq 0) { return New-DecisionResult 'REQUIRE_HUMAN_APPROVAL' 'APPROVAL_REQUIRED' }
        $matching=@($o.approval_refs | Where-Object {
            [string]$_.action_sha256 -eq [string]$a.action_sha256 -and [string]$_.intent_sha256 -eq [string]$i.intent_sha256
        })
        if ($matching.Count -eq 0) { return New-DecisionResult 'REQUIRE_HUMAN_APPROVAL' 'APPROVAL_SCOPE_MISMATCH' }
        $valid=@($matching | Where-Object { (Get-UtcDate ([string]$_.valid_until_utc)) -ge $evaluated })
        if ($valid.Count -eq 0) { return New-DecisionResult 'REQUIRE_HUMAN_APPROVAL' 'APPROVAL_EXPIRED' }
    }

    return New-DecisionResult 'ALLOW' 'ALL_CONSTRAINTS_SATISFIED'
}
