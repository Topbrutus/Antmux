Set-StrictMode -Version 2.0

function Resolve-LinuxIAInspectPath {
    param([string]$RepoRoot,[string]$UserPath,[int64]$MaxBytes=2097152)
    if([string]::IsNullOrWhiteSpace($UserPath)){throw 'CLI_FILE_REQUIRED: --file requires a relative path'}
    if([IO.Path]::IsPathRooted($UserPath)){throw 'CLI_ABSOLUTE_PATH_FORBIDDEN: absolute paths are forbidden'}
    $relative=$UserPath.Replace('\','/')
    while($relative.StartsWith('./')){$relative=$relative.Substring(2)}
    if($relative -match '[\*\?\[\]]'){throw 'CLI_WILDCARD_FORBIDDEN: wildcard characters are forbidden'}
    $segments=@($relative.Split('/') | Where-Object {$_.Length -gt 0})
    if($segments.Count -eq 0){throw 'CLI_FILE_REQUIRED: empty path'}
    if(@($segments | Where-Object {$_ -eq '..'}).Count -gt 0){throw 'CLI_PATH_TRAVERSAL: parent traversal is forbidden'}
    $blocked=@('.git','state','secrets','credentials')
    if(@($segments | Where-Object {$blocked -contains $_.ToLowerInvariant()}).Count -gt 0){throw 'CLI_PATH_SCOPE_FORBIDDEN: protected path segment'}
    $allowed=($relative -eq 'docs' -or $relative.StartsWith('docs/') -or $relative -eq 'skills' -or $relative.StartsWith('skills/'))
    if(-not $allowed){throw 'CLI_PATH_SCOPE_FORBIDDEN: only docs/** and skills/** are readable'}
    $current=(Resolve-Path -LiteralPath $RepoRoot).Path
    foreach($segment in $segments){
        $current=Join-Path $current $segment
        if(Test-Path -LiteralPath $current){
            $node=Get-Item -LiteralPath $current -Force
            if(($node.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'CLI_REPARSE_POINT_FORBIDDEN: symbolic links and junctions are forbidden'}
        }
    }
    $candidate=Join-Path $RepoRoot ($relative.Replace('/',[IO.Path]::DirectorySeparatorChar))
    if(-not (Test-Path -LiteralPath $candidate -PathType Leaf)){throw 'CLI_FILE_NOT_FOUND: target must be an existing file'}
    $resolved=(Resolve-Path -LiteralPath $candidate).Path
    $rootPrefix=(Resolve-Path -LiteralPath $RepoRoot).Path.TrimEnd('\','/')+[IO.Path]::DirectorySeparatorChar
    if(-not $resolved.StartsWith($rootPrefix,[StringComparison]::OrdinalIgnoreCase)){throw 'CLI_PATH_ESCAPE: resolved path escaped repository root'}
    $item=Get-Item -LiteralPath $resolved -Force
    if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'CLI_REPARSE_POINT_FORBIDDEN: symbolic links and junctions are forbidden'}
    if([int64]$item.Length -gt $MaxBytes){throw 'CLI_FILE_TOO_LARGE: maximum size is 2097152 bytes'}
    $repoFull=(Resolve-Path -LiteralPath $RepoRoot).Path.TrimEnd('\','/')
    $rel=$resolved.Substring($repoFull.Length).TrimStart('\','/').Replace('\','/')
    return [pscustomobject]@{full_path=$resolved;relative_path=$rel;bytes=[int64]$item.Length;last_write_time_utc=$item.LastWriteTimeUtc.ToString('o')}
}
