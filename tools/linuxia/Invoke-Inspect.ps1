Set-StrictMode -Version 2.0

function ConvertFrom-LinuxIAInspectArguments {
    param([object[]]$ArgumentList)
    $file=$null;$json=$false
    for($i=0;$i -lt @($ArgumentList).Count;$i++){
        $token=[string]$ArgumentList[$i]
        switch($token){
            '--file'{
                if($null -ne $file){throw 'CLI_DUPLICATE_FILE_ARGUMENT: --file may appear only once'}
                if($i+1 -ge @($ArgumentList).Count){throw 'CLI_FILE_VALUE_REQUIRED: --file requires a value'}
                $i++;$file=[string]$ArgumentList[$i]
            }
            '--json'{$json=$true}
            default{throw "CLI_UNKNOWN_ARGUMENT: $token"}
        }
    }
    if([string]::IsNullOrWhiteSpace($file)){throw 'CLI_FILE_REQUIRED: inspect requires --file'}
    return [pscustomobject]@{file=$file;json=$json}
}

function Get-LinuxIAIntentAuthorizerLibraryPaths {
    param([string]$RepoRoot)
    $lib=Join-Path $RepoRoot 'skills/policy.intent-authorizer.v1/tools/lib'
    $paths=@()
    foreach($name in @('Common.ps1','InputContract.ps1','Authorization.ps1','OutputContract.ps1')){
        $path=Join-Path $lib $name
        if(-not (Test-Path -LiteralPath $path -PathType Leaf)){throw "CLI_AUTHORIZER_MISSING: $path"}
        $paths+=@($path)
    }
    return $paths
}

function Invoke-LinuxIAInspect {
    param([string]$RepoRoot,[string]$File,[bool]$Audit=$true)
    $target=Resolve-LinuxIAInspectPath $RepoRoot $File
    foreach($authorizerLibrary in @(Get-LinuxIAIntentAuthorizerLibraryPaths $RepoRoot)){. $authorizerLibrary}
    $ids=New-LinuxIAExecutionIds
    $evaluated=[DateTimeOffset]::UtcNow
    $expires=$evaluated.AddMinutes(5)
    $zero='sha256:' + ('0'*64)

    $intent=[pscustomobject]@{
        schema_version='intent-envelope-v1';intent_id=$ids.intent_id;task_id=$ids.task_id;confirmed_by_user=$true
        objective=('Inspecter en lecture seule ' + $target.relative_path)
        allowed_actions=@('READ');denied_actions=@('WRITE','DELETE','PUBLISH','SEND_MESSAGE','INSTALL','ACTIVATE_MODEL')
        allowed_tools=@('source.read');resource_scopes=@([pscustomobject]@{mode='read';pattern=$target.relative_path})
        network_allowed=$false;external_effects_allowed=$false;destructive_actions_allowed=$false;max_items=1
        rent_budget=[pscustomobject]@{max_tool_calls=1;max_inference_ms=0;max_bytes_written=0}
        expires_at_utc=$expires.ToString('o');intent_sha256=$zero
    }
    $intent.intent_sha256=Get-LinuxIAObjectSha256 $intent 'intent_sha256'

    $action=[pscustomobject]@{
        schema_version='proposed-action-v1';action_id=$ids.action_id;task_id=$ids.task_id;run_id=$ids.run_id;correlation_id=$ids.correlation_id
        agent_id='linuxia-cli-01';skill_id='linuxia.inspect';skill_version='0.1.0';operation='READ';tool_name='source.read'
        arguments=[pscustomobject]@{path=$target.relative_path;mode='read';item_count=1}
        estimated_rent=[pscustomobject]@{tool_calls=1;inference_ms=0;bytes_written=0}
        external_effect=$false;destructive=$false;action_sha256=$zero
    }
    $action.action_sha256=Get-LinuxIAObjectSha256 $action 'action_sha256'

    $permissions=[pscustomobject]@{
        allowed_tools=@('source.read');denied_tools=@('filesystem.write','filesystem.delete','github.push','network.request','model.activate')
        filesystem_read=@($target.relative_path);filesystem_write=@();network_allowed=$false;current_attempt=1;max_attempts=1;permission_snapshot_sha256=$zero
    }
    $permissions.permission_snapshot_sha256=Get-LinuxIAObjectSha256 $permissions 'permission_snapshot_sha256'

    $risk=[pscustomobject]@{
        operations_requiring_approval=@('WRITE','DELETE','PUBLISH','SEND_MESSAGE','INSTALL','ACTIVATE_MODEL')
        tools_requiring_approval=@('github.push','filesystem.write','model.activate')
        destructive_requires_approval=$true;external_effect_requires_approval=$true;budget_excess_requires_approval=$true;policy_sha256=$zero
    }
    $risk.policy_sha256=Get-LinuxIAObjectSha256 $risk 'policy_sha256'

    $input=[pscustomobject]@{
        schema_version='intent-authorization-input-v1';task_id=$ids.task_id;run_id=$ids.run_id;correlation_id=$ids.correlation_id
        authorizer_id='intent-authorizer-01';intent_envelope=$intent;proposed_action=$action;permission_snapshot=$permissions;risk_policy=$risk
        approval_refs=@();current_rent=[pscustomobject]@{tool_calls=0;inference_ms=0;bytes_written=0};evaluated_at_utc=$evaluated.ToString('o')
    }
    if(-not (Test-AuthorizationInput $input)){throw 'CLI_AUTHORIZATION_INPUT_INVALID: generated authorization input failed its contract'}
    $rawDecision=Get-AuthorizationDecision $input
    $required=@();if([string]$rawDecision.decision -eq 'REQUIRE_HUMAN_APPROVAL'){$required=@($ids.action_id)}
    $matched=@();if([string]$rawDecision.decision -eq 'ALLOW'){$matched=@('tool_name','operation','resource_scope','network','rent_budget')}
    $violated=@();if([string]$rawDecision.decision -eq 'DENY'){$violated=@([string]$rawDecision.reason)}
    $decision=[pscustomobject]@{
        schema_version='intent-authorization-output-v1';decision_id=$ids.decision_id;task_id=$ids.task_id;run_id=$ids.run_id;correlation_id=$ids.correlation_id
        decision=[string]$rawDecision.decision;reason_codes=@([string]$rawDecision.reason);matched_constraints=$matched;violated_constraints=$violated;required_approvals=$required
        intent_sha256=$intent.intent_sha256;action_sha256=$action.action_sha256;permission_snapshot_sha256=$permissions.permission_snapshot_sha256;policy_sha256=$risk.policy_sha256
        decision_payload_sha256=$zero;evaluated_at_utc=$evaluated.ToString('o');expires_at_utc=$expires.ToString('o')
    }
    $decision.decision_payload_sha256=Get-LinuxIAObjectSha256 $decision 'decision_payload_sha256'
    if(-not (Test-AuthorizationOutput $decision)){throw 'CLI_AUTHORIZATION_OUTPUT_INVALID: generated decision failed its contract'}

    $decisionRel='state/decisions/'+$ids.decision_id+'.json'
    $auditRel='state/events/linuxia-cli.jsonl'
    $checkpointEventRel='state/events/checkpoints.jsonl'
    if($Audit){Write-LinuxIAImmutableJson (Join-Path $RepoRoot $decisionRel.Replace('/','\')) $decision}

    $source=$null
    $checkpoints=$null
    if($decision.decision -eq 'ALLOW'){
        $preInput=New-LinuxIACheckpointInput $ids.task_id $ids.run_id $ids.correlation_id 1 $null 'AUTHORIZED' 'PRE_ACTION' $target.relative_path $null $decisionRel $intent.intent_sha256 $action.action_sha256 $decision.decision_payload_sha256
        $preOutput=New-LinuxIACheckpointOutput $RepoRoot $preInput 'PRE_ACTION' ($evaluated.ToString('o'))
        $pre=Save-LinuxIACheckpoint $RepoRoot $preOutput $Audit

        $source=[pscustomobject]@{path=$target.relative_path;bytes=$target.bytes;sha256=(Get-LinuxIAFileSha256 $target.full_path);last_write_time_utc=$target.last_write_time_utc}

        $postInput=New-LinuxIACheckpointInput $ids.task_id $ids.run_id $ids.correlation_id 2 $pre.checkpoint_id 'RUNNING' 'POST_ACTION' $target.relative_path $source $decisionRel $intent.intent_sha256 $action.action_sha256 $decision.decision_payload_sha256
        $postOutput=New-LinuxIACheckpointOutput $RepoRoot $postInput 'POST_ACTION' ($evaluated.AddTicks(1).ToString('o'))
        $post=Save-LinuxIACheckpoint $RepoRoot $postOutput $Audit
        $checkpoints=[pscustomobject]@{
            pre_action=$pre
            post_action=$post
            chain_valid=([string]$post.parent_checkpoint_id -eq [string]$pre.checkpoint_id -and [int]$post.sequence -eq ([int]$pre.sequence+1))
            event_log=if($Audit){$checkpointEventRel}else{$null}
        }
    }

    if($Audit){
        $event=[pscustomobject]@{
            schema_version='linuxia-audit-event-v1';event_id=$ids.event_id;timestamp_utc=[DateTimeOffset]::UtcNow.ToString('o')
            task_id=$ids.task_id;run_id=$ids.run_id;correlation_id=$ids.correlation_id;command='inspect';decision=$decision.decision
            reason=[string]$rawDecision.reason;source=$source;decision_artifact=$decisionRel;checkpoints=$checkpoints
        }
        Add-LinuxIAAuditEvent (Join-Path $RepoRoot $auditRel.Replace('/','\')) $event
    }
    $status=if($decision.decision -eq 'ALLOW'){'COMPLETED'}elseif($decision.decision -eq 'DENY'){'DENIED'}else{'APPROVAL_REQUIRED'}
    return [pscustomobject]@{
        schema_version='linuxia-inspect-result-v1';status=$status;command='inspect';task_id=$ids.task_id;run_id=$ids.run_id;correlation_id=$ids.correlation_id
        decision=$decision.decision;reason=[string]$rawDecision.reason;source=$source;intent_sha256=$intent.intent_sha256;action_sha256=$action.action_sha256
        decision_artifact=if($Audit){$decisionRel}else{$null};audit_log=if($Audit){$auditRel}else{$null};checkpoints=$checkpoints
    }
}
