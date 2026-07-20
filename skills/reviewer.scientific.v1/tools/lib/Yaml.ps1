function Convert-SimpleYamlScalar {
    param([string]$RawValue)

    $value = $RawValue.Trim()
    if (
        ($value.StartsWith('"') -and $value.EndsWith('"')) -or
        ($value.StartsWith("'") -and $value.EndsWith("'"))
    ) {
        return $value.Substring(1, $value.Length - 2)
    }

    switch -Regex ($value) {
        '^(?i:true)$'  { return $true }
        '^(?i:false)$' { return $false }
        '^-?[0-9]+$'   { return [int64]$value }
        default        { return $value }
    }
}

function Read-SimpleYamlDocument {
    param([Parameter(Mandatory = $true)][string]$Path)

    $scalars = @{}
    $lists = @{}
    $stack = New-Object System.Collections.ArrayList
    $blockScalarIndent = -1

    foreach ($line in (Get-Content -LiteralPath $Path -Encoding UTF8)) {
        if ($line -match '^\s*$' -or $line -match '^\s*#') {
            continue
        }

        $indent = $line.Length - $line.TrimStart().Length

        if ($blockScalarIndent -ge 0) {
            if ($indent -gt $blockScalarIndent) {
                continue
            }
            $blockScalarIndent = -1
        }

        while (
            $stack.Count -gt 0 -and
            [int]$stack[$stack.Count - 1].indent -ge $indent
        ) {
            $stack.RemoveAt($stack.Count - 1)
        }

        if ($line -match '^\s*-\s+(.+?)\s*$') {
            $pathParts = @($stack | ForEach-Object { $_.key })
            $pathKey = $pathParts -join '.'
            if ([string]::IsNullOrWhiteSpace($pathKey)) {
                throw "YAML list item without a parent path: $line"
            }
            if (-not $lists.ContainsKey($pathKey)) {
                $lists[$pathKey] = New-Object System.Collections.ArrayList
            }
            [void]$lists[$pathKey].Add((Convert-SimpleYamlScalar -RawValue $Matches[1]))
            continue
        }

        if ($line -match '^\s*([^:#][^:]*?):(?:\s*(.*))?$') {
            $key = $Matches[1].Trim()
            $rawValue = $Matches[2]
            $parentParts = @($stack | ForEach-Object { $_.key })
            $fullPath = (@($parentParts) + $key) -join '.'

            if ([string]::IsNullOrWhiteSpace($rawValue)) {
                [void]$stack.Add([pscustomobject]@{ indent = $indent; key = $key })
                continue
            }

            $trimmedValue = $rawValue.Trim()
            if ($trimmedValue -eq '>' -or $trimmedValue -eq '|') {
                $scalars[$fullPath] = ''
                $blockScalarIndent = $indent
                continue
            }

            if ($trimmedValue -eq '[]') {
                $lists[$fullPath] = New-Object System.Collections.ArrayList
                continue
            }

            $scalars[$fullPath] = Convert-SimpleYamlScalar -RawValue $trimmedValue
            continue
        }

        throw "Unsupported YAML syntax: $line"
    }

    return [pscustomobject]@{
        scalars = $scalars
        lists   = $lists
    }
}

function Get-YamlScalar {
    param(
        [Parameter(Mandatory = $true)]$Document,
        [Parameter(Mandatory = $true)][string]$Path
    )
    if (-not $Document.scalars.ContainsKey($Path)) {
        return $null
    }
    return $Document.scalars[$Path]
}

function Get-YamlList {
    param(
        [Parameter(Mandatory = $true)]$Document,
        [Parameter(Mandatory = $true)][string]$Path
    )
    if (-not $Document.lists.ContainsKey($Path)) {
        return @()
    }
    return @($Document.lists[$Path])
}

