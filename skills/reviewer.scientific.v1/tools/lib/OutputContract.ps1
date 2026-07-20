function Test-ReviewContract {
    param($Review)

    $properties = @(
        'pattern_id', 'source_id', 'claim', 'decision', 'evidence_status',
        'reason', 'source_line_ids', 'pipeline_contamination', 'local_guardrail',
        'minimal_correction', 'risk_assessment'
    )
    if (-not (Test-ObjectPropertySet -Object $Review -Allowed $properties -Required $properties)) {
        return $false
    }

    foreach ($field in @('pattern_id', 'source_id', 'claim', 'minimal_correction')) {
        if ([string]::IsNullOrWhiteSpace([string]$Review.$field)) {
            return $false
        }
    }
    if (([string]$Review.reason).Length -lt 20) { return $false }
    if (([string]$Review.risk_assessment).Length -lt 10) { return $false }

    $decisions = @(
        'ACCEPTED', 'ANALOGY_ONLY', 'INSUFFICIENT_EVIDENCE',
        'PIPELINE_METADATA_CONTAMINATION', 'LOCAL_GUARDRAIL'
    )
    if ($decisions -notcontains [string]$Review.decision) { return $false }

    $evidenceStates = @('SUPPORTED', 'PARTIAL', 'UNSUPPORTED', 'CONTAMINATED')
    if ($evidenceStates -notcontains [string]$Review.evidence_status) { return $false }

    $lineIds = @($Review.source_line_ids)
    if (($lineIds | Sort-Object -Unique).Count -ne $lineIds.Count) { return $false }
    foreach ($lineId in $lineIds) {
        if ([string]$lineId -cnotmatch '^L[0-9]+$') { return $false }
    }

    if ([string]$Review.decision -ceq 'ACCEPTED') {
        if ([string]$Review.evidence_status -cne 'SUPPORTED') { return $false }
        if ($lineIds.Count -lt 1) { return $false }
        if ([bool]$Review.pipeline_contamination) { return $false }
        if ([bool]$Review.local_guardrail) { return $false }
    }

    if ([string]$Review.decision -ceq 'PIPELINE_METADATA_CONTAMINATION') {
        if ([string]$Review.evidence_status -cne 'CONTAMINATED') { return $false }
        if (-not [bool]$Review.pipeline_contamination) { return $false }
    }

    if ([string]$Review.decision -ceq 'LOCAL_GUARDRAIL' -and -not [bool]$Review.local_guardrail) {
        return $false
    }

    return $true
}

function Test-OutputContract {
    param($OutputObject)

    if ($null -eq $OutputObject -or $OutputObject -is [array]) {
        return $false
    }

    $topLevel = @(
        'protocol_version', 'skill_id', 'skill_version', 'task_id', 'run_id',
        'agent_id', 'correlation_id', 'reviewed_at_utc', 'input_integrity',
        'reviews', 'summary', 'result_state'
    )
    if (-not (Test-ObjectPropertySet -Object $OutputObject -Allowed $topLevel -Required $topLevel)) {
        return $false
    }

    if ([string]$OutputObject.protocol_version -cne 'antmux-mcp-v1') { return $false }
    if ([string]$OutputObject.skill_id -cne 'reviewer.scientific') { return $false }
    if ([string]$OutputObject.skill_version -cne '1.0.0') { return $false }
    if ([string]$OutputObject.task_id -cnotmatch '^TASK-[A-Za-z0-9._-]+$') { return $false }
    if ([string]$OutputObject.run_id -cnotmatch '^RUN-[A-Za-z0-9._-]+$') { return $false }
    if ([string]::IsNullOrWhiteSpace([string]$OutputObject.agent_id)) { return $false }
    if ([string]$OutputObject.correlation_id -cnotmatch '^CORR-[A-Za-z0-9._-]+$') { return $false }
    if ([string]$OutputObject.result_state -cne 'UNDER_REVIEW') { return $false }

    $parsedDate = [datetime]::MinValue
    if (-not [datetime]::TryParse(
        [string]$OutputObject.reviewed_at_utc,
        [System.Globalization.CultureInfo]::InvariantCulture,
        [System.Globalization.DateTimeStyles]::RoundtripKind,
        [ref]$parsedDate
    )) {
        return $false
    }

    $integrityNames = @(
        'worker_report_sha256', 'worker_json_sha256', 'numbered_source_sha256'
    )
    if (-not (Test-ObjectPropertySet -Object $OutputObject.input_integrity -Allowed $integrityNames -Required $integrityNames)) {
        return $false
    }
    foreach ($name in $integrityNames) {
        if (-not (Test-LowerSha256 -Value ([string]$OutputObject.input_integrity.$name))) {
            return $false
        }
    }

    $reviews = @($OutputObject.reviews)
    if ($reviews.Count -lt 1) { return $false }
    foreach ($review in $reviews) {
        if (-not (Test-ReviewContract -Review $review)) {
            return $false
        }
    }

    $summaryNames = @(
        'total', 'accepted', 'analogy_only', 'insufficient_evidence',
        'pipeline_metadata_contamination', 'local_guardrail'
    )
    if (-not (Test-ObjectPropertySet -Object $OutputObject.summary -Allowed $summaryNames -Required $summaryNames)) {
        return $false
    }

    foreach ($name in $summaryNames) {
        try {
            $value = [int64]$OutputObject.summary.$name
        }
        catch {
            return $false
        }
        if ($value -lt 0) { return $false }
    }
    if ([int64]$OutputObject.summary.total -lt 1) { return $false }
    if ([int64]$OutputObject.summary.total -ne $reviews.Count) { return $false }

    $expectedCounts = @{
        accepted                        = @($reviews | Where-Object { $_.decision -ceq 'ACCEPTED' }).Count
        analogy_only                    = @($reviews | Where-Object { $_.decision -ceq 'ANALOGY_ONLY' }).Count
        insufficient_evidence           = @($reviews | Where-Object { $_.decision -ceq 'INSUFFICIENT_EVIDENCE' }).Count
        pipeline_metadata_contamination = @($reviews | Where-Object { $_.decision -ceq 'PIPELINE_METADATA_CONTAMINATION' }).Count
        local_guardrail                 = @($reviews | Where-Object { $_.decision -ceq 'LOCAL_GUARDRAIL' }).Count
    }
    foreach ($name in $expectedCounts.Keys) {
        if ([int64]$OutputObject.summary.$name -ne [int64]$expectedCounts[$name]) {
            return $false
        }
    }

    return $true
}

function New-ValidOutputObject {
    $sha = ('b' * 64)
    return [pscustomobject]@{
        protocol_version = 'antmux-mcp-v1'
        skill_id = 'reviewer.scientific'
        skill_version = '1.0.0'
        task_id = 'TASK-VALIDATOR-001'
        run_id = 'RUN-VALIDATOR-001'
        agent_id = 'validator-local'
        correlation_id = 'CORR-VALIDATOR-001'
        reviewed_at_utc = '2026-07-20T18:00:00Z'
        input_integrity = [pscustomobject]@{
            worker_report_sha256 = $sha
            worker_json_sha256 = $sha
            numbered_source_sha256 = $sha
        }
        reviews = @(
            [pscustomobject]@{
                pattern_id = '123-P02'
                source_id = 'example-source'
                claim = 'La source décrit une validation automatique.'
                decision = 'ACCEPTED'
                evidence_status = 'SUPPORTED'
                reason = 'Les lignes citées décrivent explicitement des comparaisons automatisées.'
                source_line_ids = @('L10', 'L11')
                pipeline_contamination = $false
                local_guardrail = $false
                minimal_correction = 'Aucune correction requise.'
                risk_assessment = 'Risque faible; la preuve est directe.'
            }
        )
        summary = [pscustomobject]@{
            total = 1
            accepted = 1
            analogy_only = 0
            insufficient_evidence = 0
            pipeline_metadata_contamination = 0
            local_guardrail = 0
        }
        result_state = 'UNDER_REVIEW'
    }
}

