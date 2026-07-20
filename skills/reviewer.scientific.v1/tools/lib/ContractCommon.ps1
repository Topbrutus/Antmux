function Test-ObjectPropertySet {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string[]]$Allowed,
        [Parameter(Mandatory = $true)][string[]]$Required
    )

    if ($null -eq $Object -or $Object -isnot [psobject]) {
        return $false
    }

    $names = @($Object.PSObject.Properties.Name)
    foreach ($name in $Required) {
        if ($names -notcontains $name) {
            return $false
        }
    }
    foreach ($name in $names) {
        if ($Allowed -notcontains $name) {
            return $false
        }
    }
    return $true
}

function Test-LowerSha256 {
    param([string]$Value)
    return ($null -ne $Value -and $Value -cmatch '^[a-f0-9]{64}$')
}

function Test-NoPathTraversal {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $false
    }
    $normalized = $Path.Replace('\', '/')
    return ($normalized -notmatch '(^|/)\.\.(/|$)')
}

function Test-ArtifactContract {
    param(
        $Artifact,
        [switch]$RequireSourceId
    )

    $allowed = @('path', 'sha256', 'media_type', 'source_id')
    $required = @('path', 'sha256', 'media_type')
    if ($RequireSourceId) {
        $required += 'source_id'
    }

    if (-not (Test-ObjectPropertySet -Object $Artifact -Allowed $allowed -Required $required)) {
        return $false
    }
    if (-not (Test-NoPathTraversal -Path ([string]$Artifact.path))) {
        return $false
    }
    if (-not (Test-LowerSha256 -Value ([string]$Artifact.sha256))) {
        return $false
    }
    if (@('text/markdown', 'application/json', 'text/plain') -notcontains [string]$Artifact.media_type) {
        return $false
    }
    if ($RequireSourceId -and [string]::IsNullOrWhiteSpace([string]$Artifact.source_id)) {
        return $false
    }
    return $true
}

function Copy-JsonObject {
    param($Object)
    return ($Object | ConvertTo-Json -Depth 32 -Compress | ConvertFrom-Json)
}

