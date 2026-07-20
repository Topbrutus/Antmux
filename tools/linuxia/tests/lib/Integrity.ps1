Set-StrictMode -Version 2.0

function Test-LinuxIACliIntegrity {
    param([string]$Root)
    $registry=Get-Content -LiteralPath (Join-Path $Root 'checksums.sha256') -Encoding UTF8|Where-Object{-not [string]::IsNullOrWhiteSpace($_)}
    $expected=@{}
    foreach($line in $registry){
        if($line -match '^([0-9a-f]{64})  (.+)$'){$expected[$Matches[2]]=$Matches[1]}
        else{Add-LinuxIATestResult 'INT-REGISTRY-FORMAT' $false "Invalid checksum line: $line"}
    }
    $actualFiles=Get-ChildItem -LiteralPath $Root -Recurse -File|ForEach-Object{
        $_.FullName.Substring($Root.Length).TrimStart('\','/').Replace('\','/')
    }|Where-Object{$_ -ne 'checksums.sha256'}|Sort-Object
    Add-LinuxIATestResult 'INT-LIST' (($actualFiles-join"`n") -eq (@($expected.Keys|Sort-Object)-join"`n")) 'Checksum registry covers exactly all package files'
    foreach($rel in @($expected.Keys|Sort-Object)){
        $hash=Get-LinuxIACanonicalFileSha256 (Join-Path $Root $rel)
        Add-LinuxIATestResult ('INT-'+($rel-replace'[^A-Za-z0-9]','_').ToUpperInvariant()) ($hash -eq $expected[$rel]) "Canonical SHA-256 matches: $rel"
    }
    $launcherExpected=(Get-Content -LiteralPath (Join-Path $Root 'launcher.sha256') -Raw -Encoding UTF8).Trim()
    $launcherActual=Get-LinuxIACanonicalFileSha256 (Join-Path $Root '../linuxia.ps1')
    Add-LinuxIATestResult 'INT-LAUNCHER' ($launcherActual -eq $launcherExpected) 'Canonical SHA-256 matches root launcher'
}
