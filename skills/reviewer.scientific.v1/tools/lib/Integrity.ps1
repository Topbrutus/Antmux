function Get-NormalizedRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$FullPath
    )

    $resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
    if (-not $resolvedRoot.EndsWith([System.IO.Path]::DirectorySeparatorChar.ToString())) {
        $resolvedRoot += [System.IO.Path]::DirectorySeparatorChar
    }

    $rootUri = New-Object System.Uri -ArgumentList $resolvedRoot
    $resolvedFile = (Resolve-Path -LiteralPath $FullPath).Path
    $fileUri = New-Object System.Uri -ArgumentList $resolvedFile
    $relative = [System.Uri]::UnescapeDataString($rootUri.MakeRelativeUri($fileUri).ToString())
    return $relative.Replace('\', '/')
}

function Get-CanonicalTextSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $text = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $Path).Path, $utf8)
    $normalized = $text.Replace("`r`n", "`n").Replace("`r", "`n")
    $bytes = $utf8.GetBytes($normalized)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hashBytes = $algorithm.ComputeHash($bytes)
        return (($hashBytes | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally {
        $algorithm.Dispose()
    }
}

function Test-PackageChecksums {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$ChecksumPath
    )

    $declared = @{}
    foreach ($line in (Get-Content -LiteralPath $ChecksumPath -Encoding UTF8)) {
        if ($line -match '^\s*$') { continue }
        if ($line -cnotmatch '^([a-f0-9]{64})\s{2}(.+)$') {
            return [pscustomobject]@{
                passed = $false
                details = "Invalid checksum line: $line"
            }
        }
        $declared[$Matches[2].Replace('\', '/')] = $Matches[1]
    }

    $actualFiles = @(
        Get-ChildItem -LiteralPath $Root -Recurse -File |
        Where-Object { $_.FullName -ne (Resolve-Path -LiteralPath $ChecksumPath).Path }
    )

    $actualPaths = @()
    $normalizedLineEndings = 0
    foreach ($file in $actualFiles) {
        $relative = Get-NormalizedRelativePath -Root $Root -FullPath $file.FullName
        $actualPaths += $relative
        if (-not $declared.ContainsKey($relative)) {
            return [pscustomobject]@{
                passed = $false
                details = "File absent from checksums.sha256: $relative"
            }
        }

        $expectedHash = $declared[$relative]
        $rawHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($rawHash -cne $expectedHash) {
            $canonicalHash = Get-CanonicalTextSha256 -Path $file.FullName
            if ($canonicalHash -cne $expectedHash) {
                return [pscustomobject]@{
                    passed = $false
                    details = "SHA-256 mismatch: $relative"
                }
            }
            $normalizedLineEndings++
        }
    }

    foreach ($relative in $declared.Keys) {
        if ($actualPaths -notcontains $relative) {
            return [pscustomobject]@{
                passed = $false
                details = "Checksum references a missing file: $relative"
            }
        }
    }

    return [pscustomobject]@{
        passed = $true
        details = "$($actualPaths.Count) files verified; line-ending normalization=$normalizedLineEndings"
    }
}

