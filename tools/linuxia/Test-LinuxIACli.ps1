[CmdletBinding()]
param([string]$CliRoot=$PSScriptRoot,[switch]$PassThru)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$script:Results=New-Object System.Collections.ArrayList
. (Join-Path $CliRoot 'lib/Common.ps1')
. (Join-Path $CliRoot 'lib/CanonicalJson.ps1')
. (Join-Path $CliRoot 'lib/PathPolicy.ps1')
. (Join-Path $CliRoot 'lib/Audit.ps1')
. (Join-Path $CliRoot 'lib/Checkpoint.ps1')
. (Join-Path $CliRoot 'Invoke-Inspect.ps1')
. (Join-Path $CliRoot 'tests/lib/Cases.ps1')
. (Join-Path $CliRoot 'tests/lib/Integrity.ps1')

try{
    $root=(Resolve-Path -LiteralPath $CliRoot).Path
    $repoRoot=Get-LinuxIARepoRoot $root
    Write-Host 'ANTMUX LINUXIA CLI VALIDATOR'
    Write-Host "CLI_ROOT: $root"
    Write-Host 'MODE: READ_ONLY'
    Add-LinuxIATestResult 'ENV-001' ($PSVersionTable.PSVersion.Major -eq 5 -and $PSVersionTable.PSVersion.Minor -ge 1) ("PowerShell 5.1 compatibility :: "+$PSVersionTable.PSVersion)
    $required=@(
      'README.md','cli.ps1','Invoke-Inspect.ps1','Test-LinuxIACli.ps1','launcher.sha256',
      'schemas/inspect-result.schema.json','schemas/audit-event.schema.json','tests/cli.tests.json',
      'tests/lib/Cases.ps1','tests/lib/Integrity.ps1','lib/Common.ps1','lib/CanonicalJson.ps1',
      'lib/PathPolicy.ps1','lib/Audit.ps1','lib/Checkpoint.ps1','checksums.sha256'
    )
    foreach($rel in $required){Add-LinuxIATestResult ('FILE-'+($rel-replace'[^A-Za-z0-9]','_').ToUpperInvariant()) (Test-Path -LiteralPath (Join-Path $root $rel) -PathType Leaf) "Required file exists: $rel"}
    Add-LinuxIATestResult 'FILE-LAUNCHER' (Test-Path -LiteralPath (Join-Path $root '../linuxia.ps1') -PathType Leaf) 'Root launcher exists: tools/linuxia.ps1'
    foreach($rel in @('schemas/inspect-result.schema.json','schemas/audit-event.schema.json','tests/cli.tests.json')){
        $null=Get-Content -LiteralPath (Join-Path $root $rel) -Raw -Encoding UTF8|ConvertFrom-Json
        Add-LinuxIATestResult ('JSON-'+($rel-replace'[^A-Za-z0-9]','_').ToUpperInvariant()) $true "JSON parses: $rel"
    }
    $inspectSchema=Get-Content -LiteralPath (Join-Path $root 'schemas/inspect-result.schema.json') -Raw -Encoding UTF8|ConvertFrom-Json
    $auditSchema=Get-Content -LiteralPath (Join-Path $root 'schemas/audit-event.schema.json') -Raw -Encoding UTF8|ConvertFrom-Json
    Add-LinuxIATestResult 'SCHEMA-001' ([string]$inspectSchema.PSObject.Properties['$id'].Value -eq 'antmux://schemas/linuxia-inspect-result-v1') 'Inspect result schema identifier is exact'
    Add-LinuxIATestResult 'SCHEMA-002' ([string]$auditSchema.PSObject.Properties['$id'].Value -eq 'antmux://schemas/linuxia-audit-event-v1') 'Audit event schema identifier is exact'
    $runtimeText=@('cli.ps1','Invoke-Inspect.ps1','lib/Common.ps1','lib/CanonicalJson.ps1','lib/PathPolicy.ps1','lib/Audit.ps1','lib/Checkpoint.ps1')|ForEach-Object{Get-Content -LiteralPath (Join-Path $root $_) -Raw -Encoding UTF8}|Out-String
    foreach($check in @(
      @('STATIC-NETWORK','(?i)Invoke-WebRequest|Invoke-RestMethod|System\.Net\.Http|WebClient'),
      @('STATIC-MODEL','(?i)&\s*["'']?ollama\b|Start-Process[^`n]*ollama'),
      @('STATIC-PROCESS','(?i)Start-Process|System\.Diagnostics\.Process'),
      @('STATIC-DELETE','(?i)Remove-Item|File\.Delete|Directory\.Delete'),
      @('STATIC-GITHUB','(?i)(^|\s)gh\s+|git\s+push')
    )){Add-LinuxIATestResult $check[0] (-not ($runtimeText -match $check[1])) "Forbidden runtime capability absent: $($check[0])"}
    Add-LinuxIATestResult 'STATIC-AUTHORIZER' ($runtimeText -match 'Get-AuthorizationDecision') 'CLI calls the validated intent authorizer'
    Add-LinuxIATestResult 'STATIC-CHECKPOINT' ($runtimeText -match 'Test-InputContract' -and $runtimeText -match 'Test-OutputContract' -and $runtimeText -match 'state/checkpoints/') 'CLI applies state.checkpoint.v1 contracts and immutable checkpoint paths'
    Add-LinuxIATestResult 'STATIC-AUDIT' ($runtimeText -match 'FileMode]::CreateNew' -and $runtimeText -match 'FileMode]::Append') 'Audit writes are immutable or append-only'
    $suite=Get-Content -LiteralPath (Join-Path $root 'tests/cli.tests.json') -Raw -Encoding UTF8|ConvertFrom-Json
    Add-LinuxIATestResult 'SUITE-001' ([int]$suite.expected_count -eq 27 -and @($suite.tests).Count -eq 27) 'CLI suite count is exact'
    Invoke-LinuxIACliCases $suite $repoRoot
    Test-LinuxIACliIntegrity $root
}catch{Write-Host ('FATAL: '+$_.Exception.Message);Add-LinuxIATestResult 'FATAL' $false $_.Exception.Message}
$passed=@($script:Results|Where-Object{$_.passed}).Count
$failed=@($script:Results|Where-Object{-not $_.passed}).Count
Write-Host "`nTOTAL: $($script:Results.Count)";Write-Host "PASSED: $passed";Write-Host "FAILED: $failed"
if($failed-eq0){Write-Host 'ALL_TESTS: PASS'}else{Write-Host 'ALL_TESTS: FAIL'}
if($PassThru){[pscustomobject]@{total=$script:Results.Count;passed=$passed;failed=$failed;all_tests=($failed-eq0);results=@($script:Results)}}
$exitCode=if($failed-eq0){0}else{1}
exit $exitCode
