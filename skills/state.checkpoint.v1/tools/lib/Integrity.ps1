Set-StrictMode -Version 2.0

function Get-CanonicalSha256 {
    param([string]$Path)
    $text=[IO.File]::ReadAllText($Path).Replace("`r`n","`n").Replace("`r","`n")
    $bytes=(New-Object Text.UTF8Encoding($false)).GetBytes($text)
    $sha=[Security.Cryptography.SHA256]::Create()
    try { $hash=$sha.ComputeHash($bytes) } finally { $sha.Dispose() }
    return ([BitConverter]::ToString($hash)).Replace('-','').ToLowerInvariant()
}

function Test-PackageIntegrity {
    param([string]$Root)
    $checksumPath=Join-Path $Root 'checksums.sha256'
    $expected=@{}
    foreach ($line in Get-Content -LiteralPath $checksumPath -Encoding UTF8) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line -notmatch '^([0-9a-f]{64})  (.+)$') { Add-TestResult 'INT-FORMAT' $false 'Invalid checksum line';return }
        $expected[$Matches[2]]=$Matches[1]
    }
    $actual=@(Get-ChildItem -LiteralPath $Root -Recurse -File | Where-Object {$_.FullName -ne $checksumPath} | ForEach-Object {$_.FullName.Substring($Root.Length).TrimStart([char[]]@('\','/')).Replace('\','/')} | Sort-Object)
    $listed=@($expected.Keys | Sort-Object)
    Add-TestResult 'INT-LIST' (($actual -join "`n") -eq ($listed -join "`n")) 'Checksum registry covers exactly all files'
    foreach ($rel in $listed) {
        $path=Join-Path $Root $rel
        $raw=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        $canon=Get-CanonicalSha256 $path
        Add-TestResult ('INT-' + ($rel -replace '[^A-Za-z0-9]','_').ToUpperInvariant()) ($expected[$rel] -eq $raw -or $expected[$rel] -eq $canon) "SHA-256 matches: $rel"
    }
}
