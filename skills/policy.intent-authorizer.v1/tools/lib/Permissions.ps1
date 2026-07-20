Set-StrictMode -Version 2.0

function Get-PermissionDecision {
    param([string]$Tool,[string]$Mode,[string]$Path,[string]$TaskId,[int]$Attempt,[string[]]$Manifest)
    if ([string]::IsNullOrWhiteSpace($TaskId)) { return 'DENY/EXECUTION_IDENTITY_INVALID' }
    $max=[int](Get-YamlScalar $Manifest 'execution.max_attempts')
    if ($Attempt -gt $max) { return 'DENY/MAX_ATTEMPTS_EXCEEDED' }
    if ($Mode -eq 'network') { return 'DENY/NETWORK_NOT_ALLOWED' }
    $allow=@(Get-YamlList $Manifest 'permissions.tools.allow')
    if ($allow -notcontains $Tool) { return 'DENY/TOOL_NOT_ALLOWED' }
    if ($Mode -eq 'read' -or $Mode -eq 'write') {
        if (-not (Test-SafePath $Path)) {
            if ($Path.Replace('\','/').Split('/') -contains '..') { return 'DENY/PATH_TRAVERSAL' }
            return 'DENY/PATH_NOT_ALLOWED'
        }
        $patterns=if($Mode -eq 'read'){@(Get-YamlList $Manifest 'permissions.filesystem.read')}else{@(Get-YamlList $Manifest 'permissions.filesystem.write')}
        if (-not (Test-PathMatches $Path $patterns)) { return 'DENY/PATH_NOT_ALLOWED' }
    }
    return 'ALLOW/'
}
