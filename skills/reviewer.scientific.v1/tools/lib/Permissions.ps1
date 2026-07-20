function Test-PathPattern {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Pattern
    )
    $normalizedPath = $Path.Replace('\', '/')
    $normalizedPattern = $Pattern.Replace('\', '/').Replace('**', '*')
    return ($normalizedPath -like $normalizedPattern)
}

function Test-PathAllowed {
    param(
        [string]$Path,
        [string[]]$AllowPatterns,
        [string[]]$DenyPatterns
    )

    if (-not (Test-NoPathTraversal -Path $Path)) {
        return [pscustomobject]@{ allowed = $false; error_code = 'PATH_TRAVERSAL' }
    }

    foreach ($pattern in $DenyPatterns) {
        if (Test-PathPattern -Path $Path -Pattern $pattern) {
            return [pscustomobject]@{ allowed = $false; error_code = 'PATH_NOT_ALLOWED' }
        }
    }

    foreach ($pattern in $AllowPatterns) {
        if (Test-PathPattern -Path $Path -Pattern $pattern) {
            return [pscustomobject]@{ allowed = $true; error_code = $null }
        }
    }

    return [pscustomobject]@{ allowed = $false; error_code = 'PATH_NOT_ALLOWED' }
}

function Invoke-PermissionDecision {
    param(
        $TestCase,
        $Manifest
    )

    $maxAttempts = [int64](Get-YamlScalar -Document $Manifest -Path 'execution.max_attempts')
    if ($TestCase.PSObject.Properties.Name -contains 'attempt') {
        if ([int64]$TestCase.attempt -gt $maxAttempts) {
            return [pscustomobject]@{ decision = 'DENY'; error_code = 'MAX_ATTEMPTS_EXCEEDED' }
        }
    }

    if ($TestCase.PSObject.Properties.Name -contains 'missing') {
        $missing = @($TestCase.missing)
        if (
            $missing -contains 'task_id' -or
            $missing -contains 'run_id' -or
            $missing -contains 'agent_id' -or
            $missing -contains 'correlation_id'
        ) {
            return [pscustomobject]@{ decision = 'DENY'; error_code = 'EXECUTION_IDENTITY_INVALID' }
        }
    }

    $networkAllowed = [bool](Get-YamlScalar -Document $Manifest -Path 'permissions.network.allowed')
    if (
        [string]$TestCase.tool -ceq 'network.request' -or
        $TestCase.PSObject.Properties.Name -contains 'target'
    ) {
        if (-not $networkAllowed) {
            return [pscustomobject]@{ decision = 'DENY'; error_code = 'NETWORK_NOT_ALLOWED' }
        }
    }

    $allowedTools = @(Get-YamlList -Document $Manifest -Path 'permissions.tools.allow')
    $deniedTools = @(Get-YamlList -Document $Manifest -Path 'permissions.tools.deny')
    $tool = [string]$TestCase.tool

    if ($deniedTools -contains $tool -or $allowedTools -notcontains $tool) {
        return [pscustomobject]@{ decision = 'DENY'; error_code = 'TOOL_NOT_ALLOWED' }
    }

    if ($TestCase.PSObject.Properties.Name -contains 'path') {
        $path = [string]$TestCase.path
        $denyPaths = @(Get-YamlList -Document $Manifest -Path 'permissions.filesystem.deny')
        if ($tool -ceq 'review.write') {
            $allowPaths = @(Get-YamlList -Document $Manifest -Path 'permissions.filesystem.write')
        }
        else {
            $allowPaths = @(Get-YamlList -Document $Manifest -Path 'permissions.filesystem.read')
        }

        $pathDecision = Test-PathAllowed -Path $path -AllowPatterns $allowPaths -DenyPatterns $denyPaths
        if (-not $pathDecision.allowed) {
            return [pscustomobject]@{ decision = 'DENY'; error_code = $pathDecision.error_code }
        }
    }

    return [pscustomobject]@{ decision = 'ALLOW'; error_code = $null }
}


