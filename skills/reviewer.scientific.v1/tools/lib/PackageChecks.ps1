function Invoke-PackageChecks {
    param([Parameter(Mandatory = $true)][string]$Root)

    $requiredFiles = @(
        'README.md',
        'skill.yaml',
        'instructions.md',
        'prompts/review-pattern.md',
        'resources/evidence-rules.md',
        'resources/decision-classes.md',
        'schemas/input.schema.json',
        'schemas/output.schema.json',
        'tests/manifest.tests.json',
        'tests/permissions.tests.json',
        'tests/contracts.tests.json',
        'tools/Test-ReviewerScientificSkill.ps1',
        'tools/lib/Yaml.ps1',
        'tools/lib/ContractCommon.ps1',
        'tools/lib/InputContract.ps1',
        'tools/lib/OutputContract.ps1',
        'tools/lib/Permissions.ps1',
        'tools/lib/Integrity.ps1',
        'tools/lib/PackageChecks.ps1',
        'tools/lib/PermissionChecks.ps1',
        'tools/lib/ContractChecks.ps1',
        'checksums.sha256'
    )

    foreach ($relativePath in $requiredFiles) {
        $fullPath = Join-Path $Root $relativePath
        Add-ValidationResult -Id ('FILE-' + ($relativePath -replace '[^A-Za-z0-9]', '_').ToUpperInvariant()) `
            -Passed (Test-Path -LiteralPath $fullPath -PathType Leaf) `
            -Message "Required file exists: $relativePath"
    }

    $manifestPath = Join-Path $Root 'skill.yaml'
    $manifest = Read-SimpleYamlDocument -Path $manifestPath

    $manifestAssertions = @(
        @{ id = 'MAN-001'; path = 'schema_version'; expected = 'antmux-agent-skill-v1' },
        @{ id = 'MAN-002'; path = 'skill_id'; expected = 'reviewer.scientific' },
        @{ id = 'MAN-003'; path = 'permissions.default_deny'; expected = $true },
        @{ id = 'MAN-004'; path = 'loading.mode'; expected = 'progressive' },
        @{ id = 'MAN-005'; path = 'loading.metadata_first'; expected = $true },
        @{ id = 'MAN-006'; path = 'permissions.network.allowed'; expected = $false },
        @{ id = 'MAN-007'; path = 'safety.destructive'; expected = $false },
        @{ id = 'MAN-008'; path = 'safety.open_world'; expected = $false },
        @{ id = 'MAN-009'; path = 'safety.mutation_allowed'; expected = $false },
        @{ id = 'MAN-010'; path = 'validation.require_checksums'; expected = $true }
    )

    foreach ($assertion in $manifestAssertions) {
        $actual = Get-YamlScalar -Document $manifest -Path $assertion.path
        Add-ValidationResult -Id $assertion.id `
            -Passed ($actual -ceq $assertion.expected) `
            -Message "Manifest assertion: $($assertion.path)" `
            -Details "expected=$($assertion.expected); actual=$actual"
    }

    $allowedTools = @(Get-YamlList -Document $manifest -Path 'permissions.tools.allow')
    $deniedTools = @(Get-YamlList -Document $manifest -Path 'permissions.tools.deny')
    $intersection = @($allowedTools | Where-Object { $deniedTools -contains $_ })
    Add-ValidationResult -Id 'MAN-011' `
        -Passed ($intersection.Count -eq 0) `
        -Message 'Allowed and denied tool lists do not overlap' `
        -Details ($intersection -join ', ')

    $referencedFiles = @(
        Get-YamlList -Document $manifest -Path 'loading.instructions'
        Get-YamlList -Document $manifest -Path 'loading.prompts'
        Get-YamlList -Document $manifest -Path 'loading.resources'
        Get-YamlScalar -Document $manifest -Path 'inputs.schema'
        Get-YamlScalar -Document $manifest -Path 'outputs.schema'
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) }

    $missingReferences = @(
        $referencedFiles | Where-Object {
            -not (Test-Path -LiteralPath (Join-Path $Root ([string]$_)) -PathType Leaf)
        }
    )
    Add-ValidationResult -Id 'MAN-012' `
        -Passed ($missingReferences.Count -eq 0) `
        -Message 'All manifest references resolve to package files' `
        -Details ($missingReferences -join ', ')

    foreach ($jsonRelativePath in @(
        'schemas/input.schema.json',
        'schemas/output.schema.json',
        'tests/manifest.tests.json',
        'tests/permissions.tests.json',
        'tests/contracts.tests.json'
    )) {
        $jsonPath = Join-Path $Root $jsonRelativePath
        $passed = $true
        $details = ''
        try {
            $null = Get-Content -LiteralPath $jsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
        }
        catch {
            $passed = $false
            $details = $_.Exception.Message
        }
        Add-ValidationResult -Id ('JSON-' + ($jsonRelativePath -replace '[^A-Za-z0-9]', '_').ToUpperInvariant()) `
            -Passed $passed `
            -Message "JSON parses: $jsonRelativePath" `
            -Details $details
    }

    $manifestSuite = Get-Content -LiteralPath (Join-Path $Root 'tests/manifest.tests.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $permissionSuite = Get-Content -LiteralPath (Join-Path $Root 'tests/permissions.tests.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $contractSuite = Get-Content -LiteralPath (Join-Path $Root 'tests/contracts.tests.json') -Raw -Encoding UTF8 | ConvertFrom-Json

    Add-ValidationResult -Id 'SUITE-MANIFEST' `
        -Passed (
            [string]$manifestSuite.schema_version -ceq 'antmux-declarative-tests-v1' -and
            [string]$manifestSuite.required_result -ceq 'ALL_TESTS: PASS' -and
            @($manifestSuite.tests).Count -eq 12
        ) `
        -Message 'Manifest suite metadata and test count are exact'

    Add-ValidationResult -Id 'SUITE-PERMISSIONS' `
        -Passed (
            [string]$permissionSuite.schema_version -ceq 'antmux-declarative-tests-v1' -and
            [string]$permissionSuite.required_result -ceq 'ALL_TESTS: PASS' -and
            @($permissionSuite.tests).Count -eq 13
        ) `
        -Message 'Permission suite metadata and test count are exact'

    Add-ValidationResult -Id 'SUITE-CONTRACTS' `
        -Passed (
            [string]$contractSuite.schema_version -ceq 'antmux-declarative-tests-v1' -and
            [string]$contractSuite.required_result -ceq 'ALL_TESTS: PASS' -and
            @($contractSuite.tests).Count -eq 15
        ) `
        -Message 'Contract suite metadata and test count are exact'

    $inputSchema = Get-Content -LiteralPath (Join-Path $Root 'schemas/input.schema.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $outputSchema = Get-Content -LiteralPath (Join-Path $Root 'schemas/output.schema.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    Add-ValidationResult -Id 'SCHEMA-001' `
        -Passed ([string]$inputSchema.'$id' -ceq 'antmux://skills/reviewer.scientific.v1/input.schema.json') `
        -Message 'Input schema identifier is exact'
    Add-ValidationResult -Id 'SCHEMA-002' `
        -Passed ([string]$outputSchema.'$id' -ceq 'antmux://skills/reviewer.scientific.v1/output.schema.json') `
        -Message 'Output schema identifier is exact'

    return [pscustomobject]@{
        manifest = $manifest
        permission_suite = $permissionSuite
        contract_suite = $contractSuite
    }
}
