function Invoke-ContractChecks {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)]$ContractSuite
    )

    $validInput = New-ValidInputObject
    $validOutput = New-ValidOutputObject

    foreach ($testCase in @($ContractSuite.tests)) {
        $actualPassed = $false
        switch ([string]$testCase.id) {
            'CON-001' {
                $actualPassed = Test-InputContract -InputObject (Copy-JsonObject $validInput)
            }
            'CON-002' {
                $candidate = Copy-JsonObject $validInput
                $candidate.PSObject.Properties.Remove('task_id')
                $actualPassed = -not (Test-InputContract -InputObject $candidate)
            }
            'CON-003' {
                $candidate = Copy-JsonObject $validInput
                $candidate.inputs.worker_report.sha256 = ('A' * 64)
                $actualPassed = -not (Test-InputContract -InputObject $candidate)
            }
            'CON-004' {
                $candidate = Copy-JsonObject $validInput
                $candidate.inputs.worker_report.path = 'inputs/../secrets/key.txt'
                $actualPassed = -not (Test-InputContract -InputObject $candidate)
            }
            'CON-005' {
                $actualPassed = Test-OutputContract -OutputObject (Copy-JsonObject $validOutput)
            }
            'CON-006' {
                $actualPassed = -not (Test-OutputContract -OutputObject @(
                    (Copy-JsonObject $validOutput),
                    (Copy-JsonObject $validOutput)
                ))
            }
            'CON-007' {
                $candidate = Copy-JsonObject $validOutput
                $candidate.reviews[0].source_line_ids = @()
                $actualPassed = -not (Test-OutputContract -OutputObject $candidate)
            }
            'CON-008' {
                $candidate = Copy-JsonObject $validOutput
                $candidate.reviews[0].evidence_status = 'PARTIAL'
                $actualPassed = -not (Test-OutputContract -OutputObject $candidate)
            }
            'CON-009' {
                $candidate = Copy-JsonObject $validOutput
                $candidate.reviews[0].decision = 'PIPELINE_METADATA_CONTAMINATION'
                $candidate.reviews[0].evidence_status = 'CONTAMINATED'
                $candidate.reviews[0].pipeline_contamination = $false
                $candidate.summary.accepted = 0
                $candidate.summary.pipeline_metadata_contamination = 1
                $actualPassed = -not (Test-OutputContract -OutputObject $candidate)
            }
            'CON-010' {
                $candidate = Copy-JsonObject $validOutput
                $candidate.result_state = 'VALIDATED'
                $actualPassed = -not (Test-OutputContract -OutputObject $candidate)
            }
            'CON-011' {
                $candidate = Copy-JsonObject $validOutput
                $candidate.reviews[0].decision = 'UNKNOWN'
                $candidate.summary.accepted = 0
                $actualPassed = -not (Test-OutputContract -OutputObject $candidate)
            }
            'CON-012' {
                $candidate = Copy-JsonObject $validOutput
                $candidate | Add-Member -NotePropertyName undeclared -NotePropertyValue 'forbidden'
                $actualPassed = -not (Test-OutputContract -OutputObject $candidate)
            }
            'CON-013' {
                $candidate = Copy-JsonObject $validOutput
                $candidate.summary.total = 2
                $actualPassed = -not (Test-OutputContract -OutputObject $candidate)
            }
            'CON-014' {
                $candidate = Copy-JsonObject $validOutput
                $candidate.summary.accepted = 0
                $candidate.summary.analogy_only = 1
                $actualPassed = -not (Test-OutputContract -OutputObject $candidate)
            }
            'CON-015' {
                $checksumResult = Test-PackageChecksums `
                    -Root $Root `
                    -ChecksumPath (Join-Path $Root 'checksums.sha256')
                $actualPassed = $checksumResult.passed
            }
            default {
                $actualPassed = $false
            }
        }

        Add-ValidationResult -Id ([string]$testCase.id) `
            -Passed $actualPassed `
            -Message "Contract case: $($testCase.case)"
    }
}
