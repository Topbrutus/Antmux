Set-StrictMode -Version 2.0

function Get-LinuxIAExpectedErrorCode {
    param([scriptblock]$Action)
    try{& $Action;return ''}catch{return Get-LinuxIAErrorCode $_}
}

function Invoke-LinuxIACliCases {
    param($Suite,[string]$RepoRoot)
    $inspectCache=$null
    foreach($t in @($Suite.tests)){
        $actual=$null
        switch([string]$t.subject){
            'arguments'{
                switch([string]$t.case){
                    'valid'{$x=ConvertFrom-LinuxIAInspectArguments @('--file','docs/architecture/ANTMUX-AGENT-SKILL-V1.md');$actual=($x.file -like 'docs/*' -and -not $x.json)}
                    'json'{$x=ConvertFrom-LinuxIAInspectArguments @('--file','docs/architecture/ANTMUX-AGENT-SKILL-V1.md','--json');$actual=[bool]$x.json}
                    'missing_file'{$actual=Get-LinuxIAExpectedErrorCode {ConvertFrom-LinuxIAInspectArguments @()}}
                    'missing_value'{$actual=Get-LinuxIAExpectedErrorCode {ConvertFrom-LinuxIAInspectArguments @('--file')}}
                    'unknown'{$actual=Get-LinuxIAExpectedErrorCode {ConvertFrom-LinuxIAInspectArguments @('--wat')}}
                    'duplicate'{$actual=Get-LinuxIAExpectedErrorCode {ConvertFrom-LinuxIAInspectArguments @('--file','docs/x','--file','docs/y')}}
                }
            }
            'path'{
                switch([string]$t.case){
                    'docs_valid'{$actual=(Resolve-LinuxIAInspectPath $RepoRoot 'docs/architecture/ANTMUX-AGENT-SKILL-V1.md').relative_path -like 'docs/*'}
                    'skills_valid'{$actual=(Resolve-LinuxIAInspectPath $RepoRoot 'skills/policy.intent-authorizer.v1/README.md').relative_path -like 'skills/*'}
                    'traversal'{$actual=Get-LinuxIAExpectedErrorCode {Resolve-LinuxIAInspectPath $RepoRoot '../README.md'}}
                    'absolute'{$actual=Get-LinuxIAExpectedErrorCode {Resolve-LinuxIAInspectPath $RepoRoot 'C:\Windows\win.ini'}}
                    'git'{$actual=Get-LinuxIAExpectedErrorCode {Resolve-LinuxIAInspectPath $RepoRoot 'docs/.git/config'}}
                    'secrets'{$actual=Get-LinuxIAExpectedErrorCode {Resolve-LinuxIAInspectPath $RepoRoot 'docs/secrets/x'}}
                    'state'{$actual=Get-LinuxIAExpectedErrorCode {Resolve-LinuxIAInspectPath $RepoRoot 'docs/state/x'}}
                    'outside'{$actual=Get-LinuxIAExpectedErrorCode {Resolve-LinuxIAInspectPath $RepoRoot 'README.md'}}
                    'wildcard'{$actual=Get-LinuxIAExpectedErrorCode {Resolve-LinuxIAInspectPath $RepoRoot 'docs/*.md'}}
                    'missing'{$actual=Get-LinuxIAExpectedErrorCode {Resolve-LinuxIAInspectPath $RepoRoot 'docs/does-not-exist.md'}}
                    'directory'{$actual=Get-LinuxIAExpectedErrorCode {Resolve-LinuxIAInspectPath $RepoRoot 'docs'}}
                }
            }
            'hash'{
                if([string]$t.case -eq 'stable'){$actual=(Get-LinuxIAStringSha256 'abc') -eq (Get-LinuxIAStringSha256 'abc')}
                if([string]$t.case -eq 'property_order'){$a=[pscustomobject]@{b=2;a=1};$b=[pscustomobject]@{a=1;b=2};$actual=(Get-LinuxIAObjectSha256 $a) -eq (Get-LinuxIAObjectSha256 $b)}
            }
            {$_ -in @('inspect','checkpoint')}{
                if($null -eq $inspectCache){$inspectCache=Invoke-LinuxIAInspect $RepoRoot 'docs/architecture/ANTMUX-AGENT-SKILL-V1.md' $false}
                if([string]$t.subject -eq 'inspect'){
                    if([string]$t.case -eq 'allow_docs'){$actual=($inspectCache.decision -eq 'ALLOW' -and $inspectCache.status -eq 'COMPLETED' -and $null -eq $inspectCache.audit_log)}
                    if([string]$t.case -eq 'source_hash'){$resolved=Resolve-LinuxIAInspectPath $RepoRoot 'docs/architecture/ANTMUX-AGENT-SKILL-V1.md';$actual=$inspectCache.source.sha256 -eq (Get-LinuxIAFileSha256 $resolved.full_path)}
                }else{
                    $pre=$inspectCache.checkpoints.pre_action
                    $post=$inspectCache.checkpoints.post_action
                    switch([string]$t.case){
                        'pre_exists'{$actual=$null -ne $pre}
                        'pre_root'{$actual=([int]$pre.sequence -eq 1 -and $null -eq $pre.parent_checkpoint_id)}
                        'post_child'{$actual=([int]$post.sequence -eq 2 -and [string]$post.parent_checkpoint_id -eq [string]$pre.checkpoint_id -and [bool]$inspectCache.checkpoints.chain_valid)}
                        'states'{$actual=([string]$pre.task_state -eq 'AUTHORIZED' -and [string]$post.task_state -eq 'RUNNING')}
                        'ids'{$actual=([string]$pre.checkpoint_id -cmatch '^CHK-[A-Z0-9-]{3,160}$' -and [string]$post.checkpoint_id -cmatch '^CHK-[A-Z0-9-]{3,160}$')}
                        'no_audit_writes'{$actual=($null -eq $pre.artifact -and $null -eq $post.artifact -and $null -eq $inspectCache.checkpoints.event_log)}
                    }
                }
            }
        }
        $ok=if($t.expected -is [bool]){[bool]$actual -eq [bool]$t.expected}else{[string]$actual -eq [string]$t.expected}
        Add-LinuxIATestResult ([string]$t.id) $ok ("CLI case: "+$t.case+"; expected="+$t.expected+"; actual="+$actual)
    }
}
