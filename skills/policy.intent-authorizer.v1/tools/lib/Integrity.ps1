Set-StrictMode -Version 2.0

function Get-CanonicalTextSha256 {
    param([string]$Path)

    $bytes=[System.IO.File]::ReadAllBytes($Path)
    if($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        $withoutBom=New-Object byte[] ($bytes.Length-3)
        [System.Array]::Copy($bytes,3,$withoutBom,0,$withoutBom.Length)
        $bytes=$withoutBom
    }

    $utf8Strict=New-Object System.Text.UTF8Encoding($false,$true)
    $text=$utf8Strict.GetString($bytes)
    $text=$text.Replace("`r`n","`n").Replace("`r","`n")
    $text=$text.Normalize([System.Text.NormalizationForm]::FormC)
    $canonicalBytes=(New-Object System.Text.UTF8Encoding($false)).GetBytes($text)

    $sha=[System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($sha.ComputeHash($canonicalBytes))).Replace('-','').ToLowerInvariant()
    } finally {
        $sha.Dispose()
    }
}

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
        $hash=Get-CanonicalTextSha256 (Join-Path $Root $rel)
        Add-TestResult ('INT-' + ($rel -replace '[^A-Za-z0-9]','_').ToUpperInvariant()) ($hash -eq $expected[$rel]) "Canonical SHA-256 matches: $rel"
    }
}
