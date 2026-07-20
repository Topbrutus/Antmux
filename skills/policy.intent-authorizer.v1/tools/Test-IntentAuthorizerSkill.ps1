[CmdletBinding()]
param([string]$SkillRoot=(Split-Path -Parent $PSScriptRoot),[switch]$PassThru)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$script:Results=New-Object System.Collections.ArrayList

. (Join-Path $PSScriptRoot 'lib/Common.ps1')
. (Join-Path $PSScriptRoot 'lib/InputContract.ps1')
. (Join-Path $PSScriptRoot 'lib/Authorization.ps1')
. (Join-Path $PSScriptRoot 'lib/OutputContract.ps1')
. (Join-Path $PSScriptRoot 'lib/Permissions.ps1')
. (Join-Path $PSScriptRoot 'lib/Integrity.ps1')

try {
    $root=(Resolve-Path -LiteralPath $SkillRoot).Path
    Write-Host 'ANTMUX INTENT AUTHORIZER SKILL VALIDATOR'
    Write-Host "SKILL_ROOT: $root"
    Write-Host 'MODE: READ_ONLY'
    $envOk=($PSVersionTable.PSVersion.Major -eq 5 -and $PSVersionTable.PSVersion.Minor -ge 1)
    Add-TestResult 'ENV-001' $envOk ("PowerShell 5.1 compatibility :: " + $PSVersionTable.PSVersion)

    $required=@(
      'README.md','skill.yaml','instructions.md','prompts/authorize-action.md',
      'resources/decision-rules.md','resources/reason-codes.md',
      'schemas/input.schema.json','schemas/output.schema.json',
      'tests/manifest.tests.json','tests/permissions.tests.json','tests/contracts.tests.json',
      'tools/Test-IntentAuthorizerSkill.ps1','tools/lib/Common.ps1',
      'tools/lib/InputContract.ps1','tools/lib/Authorization.ps1',
      'tools/lib/OutputContract.ps1','tools/lib/Permissions.ps1',
      'tools/lib/Integrity.ps1','checksums.sha256'
    )
    foreach ($rel in $required) {
        Add-TestResult ('FILE-' + ($rel -replace '[^A-Za-z0-9]','_').ToUpperInvariant()) (Test-Path -LiteralPath (Join-Path $root $rel) -PathType Leaf) "Required file exists: $rel"
    }

    $manifest=Get-Content -LiteralPath (Join-Path $root 'skill.yaml') -Encoding UTF8
    $json=@{}
    foreach ($rel in @('schemas/input.schema.json','schemas/output.schema.json','tests/manifest.tests.json','tests/permissions.tests.json','tests/contracts.tests.json')) {
        $json[$rel]=Get-Content -LiteralPath (Join-Path $root $rel) -Raw -Encoding UTF8 | ConvertFrom-Json
        Add-TestResult ('JSON-' + ($rel -replace '[^A-Za-z0-9]','_').ToUpperInvariant()) $true "JSON parses: $rel"
    }

    $m=$json['tests/manifest.tests.json'];$p=$json['tests/permissions.tests.json'];$c=$json['tests/contracts.tests.json']
    Add-TestResult 'SUITE-MANIFEST' ([int]$m.expected_count -eq 16 -and @($m.tests).Count -eq 16) 'Manifest suite count is exact'
    Add-TestResult 'SUITE-PERMISSIONS' ([int]$p.expected_count -eq 16 -and @($p.tests).Count -eq 16) 'Permission suite count is exact'
    Add-TestResult 'SUITE-CONTRACTS' ([int]$c.expected_count -eq 38 -and @($c.tests).Count -eq 38) 'Contract suite count is exact'

    $inputSchemaId=[string]$json['schemas/input.schema.json'].PSObject.Properties['$id'].Value
    $outputSchemaId=[string]$json['schemas/output.schema.json'].PSObject.Properties['$id'].Value
    Add-TestResult 'SCHEMA-001' ($inputSchemaId -eq 'antmux://schemas/intent-authorization-input-v1') 'Input schema identifier is exact'
    Add-TestResult 'SCHEMA-002' ($outputSchemaId -eq 'antmux://schemas/intent-authorization-output-v1') 'Output schema identifier is exact'

    foreach ($t in @($m.tests)) {
        $actual=Get-YamlScalar $manifest ([string]$t.path)
        Add-TestResult ([string]$t.id) ($actual -eq $t.expected) ("Manifest assertion: " + $t.path)
    }
    $allow=@(Get-YamlList $manifest 'permissions.tools.allow')
    $deny=@(Get-YamlList $manifest 'permissions.tools.deny')
    Add-TestResult 'MAN-NO-OVERLAP' (@($allow | Where-Object {$deny -contains $_}).Count -eq 0) 'Allowed and denied tools do not overlap'
    Add-TestResult 'MAN-NO-MODELS' (@(Get-YamlList $manifest 'permissions.models.allow').Count -eq 0) 'No model is authorized'

    $references=@()
    $references += @(Get-YamlList $manifest 'loading.instructions')
    $references += @(Get-YamlList $manifest 'loading.prompts')
    $references += @(Get-YamlList $manifest 'loading.resources')
    $references += [string](Get-YamlScalar $manifest 'inputs.schema')
    $references += [string](Get-YamlScalar $manifest 'outputs.schema')
    foreach ($rel in $references) {
        Add-TestResult ('REF-' + ($rel -replace '[^A-Za-z0-9]','_').ToUpperInvariant()) (Test-Path -LiteralPath (Join-Path $root $rel)) "Manifest reference resolves: $rel"
    }

    foreach ($t in @($p.tests)) {
        $task=if(Test-HasProperty $t 'task_id'){[string]$t.task_id}else{'TASK-0042'}
        $attempt=if(Test-HasProperty $t 'attempt'){[int]$t.attempt}else{1}
        $actual=Get-PermissionDecision ([string]$t.tool) ([string]$t.mode) ([string]$t.path) $task $attempt $manifest
        $expected=([string]$t.expected)+'/'+([string]$t.reason)
        Add-TestResult ([string]$t.id) ($actual -eq $expected) "Permission decision: expected=$expected; actual=$actual"
    }

    foreach ($t in @($c.tests)) {
        $subject=[string]$t.subject
        if ($subject -eq 'input') {
            $fixture=New-AuthorizationFixture ([string]$t.case)
            $actual=Test-AuthorizationInput $fixture
            Add-TestResult ([string]$t.id) ($actual -eq [bool]$t.valid) ("Input contract case: " + $t.case)
        } elseif ($subject -eq 'output') {
            $fixture=New-OutputFixture ([string]$t.case)
            $actual=Test-AuthorizationOutput $fixture
            Add-TestResult ([string]$t.id) ($actual -eq [bool]$t.valid) ("Output contract case: " + $t.case)
        } elseif ($subject -eq 'decision') {
            $fixture=New-AuthorizationFixture ([string]$t.case)
            $result=Get-AuthorizationDecision $fixture
            $actual=([string]$result.decision)+'/'+([string]$result.reason)
            Add-TestResult ([string]$t.id) ($actual -eq [string]$t.expected) ("Decision case: expected=" + $t.expected + '; actual=' + $actual)
        } else {
            Add-TestResult ([string]$t.id) $false ("Unknown contract subject: " + $subject)
        }
    }

    Test-PackageIntegrity $root
} catch {
    Write-Host ('FATAL: ' + $_.Exception.Message)
    Add-TestResult 'FATAL' $false $_.Exception.Message
}

$passed=@($script:Results | Where-Object {$_.passed}).Count
$failed=@($script:Results | Where-Object {-not $_.passed}).Count
Write-Host "`nTOTAL: $($script:Results.Count)"
Write-Host "PASSED: $passed"
Write-Host "FAILED: $failed"
if($failed -eq 0){Write-Host 'ALL_TESTS: PASS'}else{Write-Host 'ALL_TESTS: FAIL'}
if($PassThru){[pscustomobject]@{total=$script:Results.Count;passed=$passed;failed=$failed;all_tests=($failed -eq 0);results=@($script:Results)}}
$exitCode=if($failed -eq 0){0}else{1}
exit $exitCode
