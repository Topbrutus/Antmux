Set-StrictMode -Version 2.0

function Add-TestResult {
    param([string]$Id,[bool]$Passed,[string]$Description)
    $null = $script:Results.Add([pscustomobject]@{id=$Id;passed=$Passed;description=$Description})
    $prefix = if ($Passed) { '[PASS]' } else { '[FAIL]' }
    Write-Host "$prefix $Id - $Description"
}

function Test-HasProperty {
    param($Object,[string]$Name)
    return ($null -ne $Object -and $null -ne $Object.PSObject.Properties[$Name])
}

function Get-YamlScalar {
    param([string[]]$Lines,[string]$Path)
    $stack = @{}
    foreach ($line in $Lines) {
        if ($line -match '^\s*$' -or $line -match '^\s*#') { continue }
        $indent = $line.Length - $line.TrimStart().Length
        foreach ($k in @($stack.Keys)) { if ([int]$k -ge $indent) { $stack.Remove($k) } }
        if ($line.Trim() -match '^([^:]+):(?:\s*(.*))?$') {
            $key = $Matches[1].Trim()
            $value = $Matches[2]
            $stack[$indent] = $key
            $current = (@($stack.Keys | Sort-Object {[int]$_}) | ForEach-Object { $stack[$_] }) -join '.'
            if ($current -eq $Path -and $null -ne $value -and $value.Trim().Length -gt 0) {
                $v = $value.Trim().Trim('"').Trim("'")
                if ($v -eq 'true') { return $true }
                if ($v -eq 'false') { return $false }
                if ($v -eq '[]') { return @() }
                if ($v -match '^-?\d+$') { return [int]$v }
                return $v
            }
        }
    }
    return $null
}

function Get-YamlList {
    param([string[]]$Lines,[string]$Path)
    $stack = @{}
    $items = New-Object System.Collections.ArrayList
    foreach ($line in $Lines) {
        if ($line -match '^\s*$' -or $line -match '^\s*#') { continue }
        $indent = $line.Length - $line.TrimStart().Length
        foreach ($k in @($stack.Keys)) { if ([int]$k -ge $indent) { $stack.Remove($k) } }
        $trim = $line.Trim()
        if ($trim -match '^-\s+(.+)$') {
            $current = (@($stack.Keys | Sort-Object {[int]$_}) | ForEach-Object { $stack[$_] }) -join '.'
            if ($current -eq $Path) { $null = $items.Add($Matches[1].Trim().Trim('"').Trim("'")) }
            continue
        }
        if ($trim -match '^([^:]+):') { $stack[$indent] = $Matches[1].Trim() }
    }
    return @($items)
}

function Test-Id {
    param([string]$Value,[string]$Pattern)
    return (-not [string]::IsNullOrWhiteSpace($Value) -and $Value -cmatch $Pattern)
}

function Test-Sha256 {
    param([string]$Value)
    return (-not [string]::IsNullOrWhiteSpace($Value) -and $Value -cmatch '^sha256:[0-9a-f]{64}$')
}

function Test-UtcDate {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
    $dto = [DateTimeOffset]::MinValue
    return [DateTimeOffset]::TryParse($Value,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::AssumeUniversal,[ref]$dto)
}

function Get-UtcDate {
    param([string]$Value)
    return [DateTimeOffset]::Parse($Value,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::AssumeUniversal).ToUniversalTime()
}

function Test-SafePath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    $p = $Path.Replace('\','/')
    if ($p -match '^[A-Za-z]:/' -or $p.StartsWith('/')) { return $false }
    if (@($p.Split('/') | Where-Object { $_ -eq '..' }).Count -gt 0) { return $false }
    if ($p -match '(^|/)(\.git|secrets|credentials)(/|$)') { return $false }
    return $true
}

function Test-PathMatches {
    param([string]$Path,[string[]]$Patterns)
    $p = $Path.Replace('\','/')
    foreach ($raw in @($Patterns)) {
        $pattern = $raw.Replace('\','/')
        if ($pattern.EndsWith('/**')) {
            $prefix = $pattern.Substring(0,$pattern.Length-3)
            if ($p -eq $prefix -or $p.StartsWith($prefix + '/')) { return $true }
        } elseif ($p -eq $pattern) { return $true }
    }
    return $false
}

function Test-ContainsSecretField {
    param($Value)
    if ($null -eq $Value -or $Value -is [string] -or $Value -is [ValueType]) { return $false }
    if ($Value -is [System.Collections.IEnumerable] -and -not ($Value -is [pscustomobject])) {
        foreach ($item in @($Value)) { if (Test-ContainsSecretField $item) { return $true } }
        return $false
    }
    foreach ($prop in @($Value.PSObject.Properties)) {
        if ($prop.Name -match '(?i)(password|passwd|token|cookie|api[_-]?key|secret|credential)') { return $true }
        if (Test-ContainsSecretField $prop.Value) { return $true }
    }
    return $false
}

function Test-NonNegativeInteger {
    param($Value)
    try { return ([int64]$Value -ge 0) } catch { return $false }
}

function Test-StringArray {
    param($Value)
    if ($null -eq $Value) { return $false }
    foreach ($x in @($Value)) { if ([string]::IsNullOrWhiteSpace([string]$x)) { return $false } }
    return $true
}
