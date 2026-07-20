function Test-InputContract {
    param($InputObject)

    if ($null -eq $InputObject -or $InputObject -is [array]) {
        return $false
    }

    $topLevel = @(
        'protocol_version', 'skill_id', 'skill_version', 'task_id',
        'run_id', 'agent_id', 'correlation_id', 'inputs'
    )
    if (-not (Test-ObjectPropertySet -Object $InputObject -Allowed $topLevel -Required $topLevel)) {
        return $false
    }

    if ([string]$InputObject.protocol_version -cne 'antmux-mcp-v1') { return $false }
    if ([string]$InputObject.skill_id -cne 'reviewer.scientific') { return $false }
    if ([string]$InputObject.skill_version -cne '1.0.0') { return $false }
    if ([string]$InputObject.task_id -cnotmatch '^TASK-[A-Za-z0-9._-]+$') { return $false }
    if ([string]$InputObject.run_id -cnotmatch '^RUN-[A-Za-z0-9._-]+$') { return $false }
    if ([string]::IsNullOrWhiteSpace([string]$InputObject.agent_id)) { return $false }
    if (([string]$InputObject.agent_id).Length -gt 128) { return $false }
    if ([string]$InputObject.correlation_id -cnotmatch '^CORR-[A-Za-z0-9._-]+$') { return $false }

    $inputNames = @('worker_report', 'worker_json', 'numbered_source')
    if (-not (Test-ObjectPropertySet -Object $InputObject.inputs -Allowed $inputNames -Required $inputNames)) {
        return $false
    }

    if (-not (Test-ArtifactContract -Artifact $InputObject.inputs.worker_report)) { return $false }
    if (-not (Test-ArtifactContract -Artifact $InputObject.inputs.worker_json)) { return $false }
    if (-not (Test-ArtifactContract -Artifact $InputObject.inputs.numbered_source -RequireSourceId)) { return $false }

    return $true
}

function New-ValidInputObject {
    $sha = ('a' * 64)
    return [pscustomobject]@{
        protocol_version = 'antmux-mcp-v1'
        skill_id = 'reviewer.scientific'
        skill_version = '1.0.0'
        task_id = 'TASK-VALIDATOR-001'
        run_id = 'RUN-VALIDATOR-001'
        agent_id = 'validator-local'
        correlation_id = 'CORR-VALIDATOR-001'
        inputs = [pscustomobject]@{
            worker_report = [pscustomobject]@{
                path = 'analysis/worker/example.md'
                sha256 = $sha
                media_type = 'text/markdown'
            }
            worker_json = [pscustomobject]@{
                path = 'analysis/worker/example.json'
                sha256 = $sha
                media_type = 'application/json'
            }
            numbered_source = [pscustomobject]@{
                path = 'inputs/example-source.md'
                sha256 = $sha
                media_type = 'text/markdown'
                source_id = 'example-source'
            }
        }
    }
}

