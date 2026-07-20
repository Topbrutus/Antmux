Set-StrictMode -Version 2.0

function Get-PermissionDecision {
    param([string]$Tool,[string]$Mode,[string]$Path,[string]$TaskId='TASK-0042',[int]$Attempt=1,[string[]]$ManifestLines)
    if (-not (Test-Id $TaskId '^TASK-[A-Z0-9-]{1,64}$')) { return 'DENY/EXECUTION_IDENTITY_INVALID' }
    if ($Attempt -gt [int](Get-YamlScalar $ManifestLines 'execution.max_attempts')) { return 'DENY/MAX_ATTEMPTS_EXCEEDED' }
    if ($Mode -eq 'network' -or $Tool -eq 'network.request') { return 'DENY/NETWORK_NOT_ALLOWED' }
    if (@(Get-YamlList $ManifestLines 'permissions.tools.allow') -notcontains $Tool) { return 'DENY/TOOL_NOT_ALLOWED' }
    if (-not [string]::IsNullOrWhiteSpace($Path)) {
        $p=$Path.Replace('\','/')
        if (@($p.Split('/') | Where-Object { $_ -eq '..' }).Count -gt 0) { return 'DENY/PATH_TRAVERSAL' }
        if (-not (Test-SafePath $p)) { return 'DENY/PATH_NOT_ALLOWED' }
        $patterns = if ($Mode -eq 'write') { @(Get-YamlList $ManifestLines 'permissions.filesystem.write') } else { @(Get-YamlList $ManifestLines 'permissions.filesystem.read') }
        if (-not (Test-PathMatches $p $patterns)) { return 'DENY/PATH_NOT_ALLOWED' }
    }
    return 'ALLOW/'
}
