function Invoke-PermissionChecks {
    param(
        [Parameter(Mandatory = $true)]$Manifest,
        [Parameter(Mandatory = $true)]$PermissionSuite
    )

    foreach ($testCase in @($PermissionSuite.tests)) {
        $decision = Invoke-PermissionDecision -TestCase $testCase -Manifest $Manifest
        $expectedError = $null
        if ($testCase.PSObject.Properties.Name -contains 'error_code') {
            $expectedError = [string]$testCase.error_code
        }
        $passed = (
            [string]$decision.decision -ceq [string]$testCase.expected -and
            (
                [string]$testCase.expected -ceq 'ALLOW' -or
                [string]$decision.error_code -ceq $expectedError
            )
        )
        Add-ValidationResult -Id ([string]$testCase.id) `
            -Passed $passed `
            -Message "Permission decision for $($testCase.tool)" `
            -Details "expected=$($testCase.expected)/$expectedError; actual=$($decision.decision)/$($decision.error_code)"
    }
}
