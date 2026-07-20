Set-StrictMode -Version 2.0

function Test-PackageIntegrity {
    param([string]$Root)
    $registry=Join-Path $Root 'checksums.sha256'
    $lines=Get-Content -LiteralPath $registry -Encoding UTF8 | Where-Object {-not [string]::IsNullOrWhiteSpace($_)}
    $expected=@{}
    foreach($line in $lines) {
        if($line -notmatch '^([0-9a-f]{64})  (.+)$') {
            Add-TestResult 'INT-REGISTRY-FORMAT' $false "Invalid checksum line: $line"
            continue
        }
        $expected[$Matches[2]]=$Matches[1]
    }
    $actualFiles=Get-ChildItem -LiteralPath $Root -Recurse -File | ForEach-Object {
        $_.FullName.Substring($Root.Length).TrimStart('\','/').Replace('\','/')
    } | Where-Object {$_ -ne 'checksums.sha256'} | Sort-Object
    $expectedFiles=@($expected.Keys | Sort-Object)
    Add-TestResult 'INT-LIST' (($actualFiles -join "`n") -eq ($expectedFiles -join "`n")) 'Checksum registry covers exactly all files'
    foreach($rel in $expectedFiles) {
        $hash=(Get-FileHash -LiteralPath (Join-Path $Root $rel) -Algorithm SHA256).Hash.ToLowerInvariant()
        Add-TestResult ('INT-' + ($rel -replace '[^A-Za-z0-9]','_').ToUpperInvariant()) ($hash -eq $expected[$rel]) "SHA-256 matches: $rel"
    }
}
