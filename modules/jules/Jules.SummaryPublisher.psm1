#requires -Version 5.1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-AntmuxRoot {
    if (-not [string]::IsNullOrWhiteSpace($env:ANTMUX_ROOT)) {
        return [System.IO.Path]::GetFullPath($env:ANTMUX_ROOT)
    }

    $modulesDirectory = Split-Path -Parent $PSScriptRoot
    $candidate = Split-Path -Parent $modulesDirectory
    return [System.IO.Path]::GetFullPath($candidate)
}

function Resolve-AntmuxPath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Path
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path $Root $Path))
}

function Assert-AntmuxDrive {
    param([Parameter(Mandatory = $true)][string]$Root)

    $driveRoot = [System.IO.Path]::GetPathRoot($Root)
    $drive = New-Object System.IO.DriveInfo($driveRoot)

    if (-not $drive.IsReady) {
        throw "The Antmux drive is not ready: $driveRoot"
    }

    if ($drive.VolumeLabel -ine "Antmux") {
        throw "The drive must be named Antmux. Current label: '$($drive.VolumeLabel)'."
    }
}

function Get-JulesConfig {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [string]$ConfigPath
    )

    if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
        $ConfigPath = Join-Path $Root "config\jules-summary-publisher.json"
    }

    $resolved = Resolve-AntmuxPath -Root $Root -Path $ConfigPath
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        throw "Jules configuration not found: $resolved"
    }

    $config = Get-Content -LiteralPath $resolved -Raw | ConvertFrom-Json
    foreach ($required in @(
        "repository_url",
        "branch",
        "workspace_relative",
        "destination_relative",
        "default_project_id",
        "organize_by_project",
        "commit_message_template"
    )) {
        if ($null -eq $config.PSObject.Properties[$required]) {
            throw "Missing Jules configuration property: $required"
        }
    }

    return [pscustomobject]@{
        Path = $resolved
        Data = $config
    }
}

function Get-GitCommand {
    $command = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        $command = Get-Command git -ErrorAction SilentlyContinue
    }
    if ($null -eq $command) {
        throw "Git was not found in PATH. Install Git for Windows before using Jules."
    }

    return $command.Source
}

function Invoke-JulesGit {
    param(
        [Parameter(Mandatory = $true)][string]$Git,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [switch]$AllowFailure
    )

    $previousPrompt = $env:GIT_TERMINAL_PROMPT
    $env:GIT_TERMINAL_PROMPT = "1"
    try {
        Push-Location -LiteralPath $WorkingDirectory
        try {
            $output = (& $Git @Arguments 2>&1 | Out-String).Trim()
            $exitCode = $LASTEXITCODE
        }
        finally {
            Pop-Location
        }
    }
    finally {
        $env:GIT_TERMINAL_PROMPT = $previousPrompt
    }

    if (($exitCode -ne 0) -and (-not $AllowFailure)) {
        $displayArguments = $Arguments -join " "
        throw "git $displayArguments failed with exit code $exitCode.`n$output"
    }

    return [pscustomobject]@{
        ExitCode = $exitCode
        Output = $output
    }
}

function Wait-JulesFileStable {
    param([Parameter(Mandatory = $true)][string]$Path)

    $previousLength = -1L
    $previousWrite = [datetime]::MinValue
    $stableReads = 0

    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        $item = Get-Item -LiteralPath $Path
        if (($item.Length -eq $previousLength) -and ($item.LastWriteTimeUtc -eq $previousWrite)) {
            $stableReads++
            if ($stableReads -ge 2) {
                return
            }
        }
        else {
            $stableReads = 0
            $previousLength = $item.Length
            $previousWrite = $item.LastWriteTimeUtc
        }

        Start-Sleep -Milliseconds 250
    }

    throw "The summary file did not become stable in time: $Path"
}

function Get-FrontMatterValue {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $pattern = "(?im)^\s*" + [regex]::Escape($Name) + "\s*:\s*(.+?)\s*$"
    $match = [regex]::Match($Content, $pattern)
    if (-not $match.Success) {
        return $null
    }

    $value = $match.Groups[1].Value.Trim()
    if ($value.Length -ge 2) {
        $first = $value.Substring(0, 1)
        $last = $value.Substring($value.Length - 1, 1)
        if ((($first -eq '"') -and ($last -eq '"')) -or (($first -eq "'") -and ($last -eq "'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
    }

    return $value.Trim()
}

function Get-SafeFileToken {
    param([Parameter(Mandatory = $true)][string]$Value)

    $token = [regex]::Replace($Value, "[^A-Za-z0-9_-]", "-")
    $token = [regex]::Replace($token, "-+", "-").Trim("-")
    if ([string]::IsNullOrWhiteSpace($token)) {
        return "summary"
    }
    if ($token.Length -gt 80) {
        return $token.Substring(0, 80)
    }
    return $token
}

function Resolve-ProjectId {
    param(
        [string]$Requested,
        [string]$FromContent,
        [Parameter(Mandatory = $true)][string]$Fallback
    )

    $value = $Requested
    if ([string]::IsNullOrWhiteSpace($value)) {
        $value = $FromContent
    }
    if ([string]::IsNullOrWhiteSpace($value)) {
        $value = $Fallback
    }

    $value = $value.ToUpperInvariant()
    if ($value -notmatch '^PROJECT-[0-9]{6}$') {
        throw "Invalid project id '$value'. Expected PROJECT-000000."
    }
    return $value
}

function Resolve-JobId {
    param(
        [string]$Requested,
        [string]$FromContent,
        [string]$FromFileName
    )

    foreach ($candidate in @($Requested, $FromContent, $FromFileName)) {
        if (-not [string]::IsNullOrWhiteSpace($candidate)) {
            $value = $candidate.ToUpperInvariant()
            if ($value -notmatch '^JOB-[0-9]{6}$') {
                throw "Invalid job id '$value'. Expected JOB-000001."
            }
            return $value
        }
    }

    return $null
}

function Assert-SummaryContent {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Path
    )

    if ([string]::IsNullOrWhiteSpace($Content)) {
        throw "The summary file is empty: $Path"
    }

    $startMarker = 'D(?:E|\u00C9)BUT\s+DU\s+R(?:E|\u00C9)SUM(?:E|\u00C9)'
    $endMarker = 'FIN\s+DU\s+(?:TERMINAL|R(?:E|\u00C9)SUM(?:E|\u00C9))'
    if (-not [regex]::IsMatch($Content, "(?is)$startMarker.*?$endMarker")) {
        throw "The file does not contain a complete summary block: $Path"
    }
}

function Initialize-JulesRepository {
    param(
        [Parameter(Mandatory = $true)][string]$Git,
        [Parameter(Mandatory = $true)][string]$RepositoryUrl,
        [Parameter(Mandatory = $true)][string]$Branch,
        [Parameter(Mandatory = $true)][string]$Workspace
    )

    $parent = Split-Path -Parent $Workspace
    New-Item -ItemType Directory -Force -Path $parent | Out-Null

    $gitDirectory = Join-Path $Workspace ".git"
    if (-not (Test-Path -LiteralPath $gitDirectory -PathType Container)) {
        if ((Test-Path -LiteralPath $Workspace) -and ((Get-ChildItem -LiteralPath $Workspace -Force | Measure-Object).Count -gt 0)) {
            throw "Jules workspace exists but is not an empty Git repository: $Workspace"
        }

        Invoke-JulesGit -Git $Git -Arguments @(
            "clone",
            "--branch", $Branch,
            "--single-branch",
            $RepositoryUrl,
            $Workspace
        ) -WorkingDirectory $parent | Out-Null
    }

    $remote = Invoke-JulesGit -Git $Git -Arguments @("remote", "get-url", "origin") -WorkingDirectory $Workspace
    if ($remote.Output.Trim() -ine $RepositoryUrl.Trim()) {
        throw "Unexpected Jules origin. Expected '$RepositoryUrl', found '$($remote.Output)'."
    }

    Invoke-JulesGit -Git $Git -Arguments @("fetch", "origin", $Branch) -WorkingDirectory $Workspace | Out-Null
    Invoke-JulesGit -Git $Git -Arguments @("checkout", $Branch) -WorkingDirectory $Workspace | Out-Null
    Invoke-JulesGit -Git $Git -Arguments @("pull", "--ff-only", "origin", $Branch) -WorkingDirectory $Workspace | Out-Null

    $status = Invoke-JulesGit -Git $Git -Arguments @("status", "--porcelain") -WorkingDirectory $Workspace
    if (-not [string]::IsNullOrWhiteSpace($status.Output)) {
        throw "Jules workspace contains uncommitted changes. Resolve them before publishing another summary.`n$($status.Output)"
    }
}

function Ensure-JulesGitIdentity {
    param(
        [Parameter(Mandatory = $true)][string]$Git,
        [Parameter(Mandatory = $true)][string]$Workspace,
        [Parameter(Mandatory = $true)][object]$Config
    )

    $name = Invoke-JulesGit -Git $Git -Arguments @("config", "user.name") -WorkingDirectory $Workspace -AllowFailure
    if ([string]::IsNullOrWhiteSpace($name.Output)) {
        Invoke-JulesGit -Git $Git -Arguments @("config", "user.name", [string]$Config.git_user_name) -WorkingDirectory $Workspace | Out-Null
    }

    $email = Invoke-JulesGit -Git $Git -Arguments @("config", "user.email") -WorkingDirectory $Workspace -AllowFailure
    if ([string]::IsNullOrWhiteSpace($email.Output)) {
        Invoke-JulesGit -Git $Git -Arguments @("config", "user.email", [string]$Config.git_user_email) -WorkingDirectory $Workspace | Out-Null
    }
}

function Test-AntmuxJulesPublisher {
    [CmdletBinding()]
    param([string]$ConfigPath)

    $root = Get-AntmuxRoot
    Assert-AntmuxDrive -Root $root
    $configRecord = Get-JulesConfig -Root $root -ConfigPath $ConfigPath
    $workspace = Resolve-AntmuxPath -Root $root -Path ([string]$configRecord.Data.workspace_relative)
    $git = Get-GitCommand

    return [pscustomobject]@{
        Status = "ready"
        AntmuxRoot = $root
        ConfigPath = $configRecord.Path
        Git = $git
        Workspace = $workspace
        WorkspaceInitialized = (Test-Path -LiteralPath (Join-Path $workspace ".git") -PathType Container)
        Repository = [string]$configRecord.Data.repository_url
        Branch = [string]$configRecord.Data.branch
    }
}

function Send-AntmuxSummary {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$SummaryPath,
        [string]$ProjectId,
        [string]$JobId,
        [string]$ConfigPath,
        [switch]$DryRun
    )

    $root = Get-AntmuxRoot
    Assert-AntmuxDrive -Root $root
    $configRecord = Get-JulesConfig -Root $root -ConfigPath $ConfigPath
    $config = $configRecord.Data

    $source = Resolve-AntmuxPath -Root $root -Path $SummaryPath
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Summary file not found: $source"
    }

    Wait-JulesFileStable -Path $source
    $content = Get-Content -LiteralPath $source -Raw
    Assert-SummaryContent -Content $content -Path $source

    $frontProjectId = Get-FrontMatterValue -Content $content -Name "project_id"
    $frontJobId = Get-FrontMatterValue -Content $content -Name "job_id"
    $fileJobMatch = [regex]::Match([System.IO.Path]::GetFileNameWithoutExtension($source), 'JOB-[0-9]{6}', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $fileJobId = if ($fileJobMatch.Success) { $fileJobMatch.Value } else { $null }

    $resolvedProjectId = Resolve-ProjectId -Requested $ProjectId -FromContent $frontProjectId -Fallback ([string]$config.default_project_id)
    $resolvedJobId = Resolve-JobId -Requested $JobId -FromContent $frontJobId -FromFileName $fileJobId

    $destinationDirectory = [string]$config.destination_relative
    if ([bool]$config.organize_by_project) {
        $destinationDirectory = Join-Path $destinationDirectory $resolvedProjectId
    }

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
    if ($null -ne $resolvedJobId) {
        $destinationName = "$resolvedJobId-RESUME.md"
    }
    else {
        $baseName = Get-SafeFileToken -Value ([System.IO.Path]::GetFileNameWithoutExtension($source))
        $destinationName = "UNASSIGNED-$timestamp-$baseName.md"
    }

    $workspace = Resolve-AntmuxPath -Root $root -Path ([string]$config.workspace_relative)
    $repositoryDestinationDirectory = Join-Path $workspace $destinationDirectory
    $repositoryDestination = Join-Path $repositoryDestinationDirectory $destinationName
    $relativeDestination = Join-Path $destinationDirectory $destinationName
    $gitRelativeDestination = $relativeDestination -replace '\\', '/'

    if ($DryRun) {
        return [pscustomobject]@{
            Status = "dry-run"
            Source = $source
            ProjectId = $resolvedProjectId
            JobId = $resolvedJobId
            Destination = $repositoryDestination
            GitPath = $gitRelativeDestination
        }
    }

    $lockPath = Join-Path $root ".antmux-jules-publisher.lock"
    $lockStream = $null
    try {
        $lockStream = New-Object System.IO.FileStream(
            $lockPath,
            [System.IO.FileMode]::OpenOrCreate,
            [System.IO.FileAccess]::ReadWrite,
            [System.IO.FileShare]::None
        )

        $git = Get-GitCommand
        Initialize-JulesRepository `
            -Git $git `
            -RepositoryUrl ([string]$config.repository_url) `
            -Branch ([string]$config.branch) `
            -Workspace $workspace
        Ensure-JulesGitIdentity -Git $git -Workspace $workspace -Config $config

        New-Item -ItemType Directory -Force -Path $repositoryDestinationDirectory | Out-Null

        if (Test-Path -LiteralPath $repositoryDestination -PathType Leaf) {
            $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
            $destinationHash = (Get-FileHash -LiteralPath $repositoryDestination -Algorithm SHA256).Hash
            if ($sourceHash -eq $destinationHash) {
                return [pscustomobject]@{
                    Status = "already-published"
                    ProjectId = $resolvedProjectId
                    JobId = $resolvedJobId
                    Destination = $repositoryDestination
                    GitPath = $gitRelativeDestination
                }
            }

            $nameWithoutExtension = [System.IO.Path]::GetFileNameWithoutExtension($destinationName)
            $destinationName = "$nameWithoutExtension-$timestamp.md"
            $repositoryDestination = Join-Path $repositoryDestinationDirectory $destinationName
            $relativeDestination = Join-Path $destinationDirectory $destinationName
            $gitRelativeDestination = $relativeDestination -replace '\\', '/'
        }

        Copy-Item -LiteralPath $source -Destination $repositoryDestination -Force
        Invoke-JulesGit -Git $git -Arguments @("add", "--", $gitRelativeDestination) -WorkingDirectory $workspace | Out-Null

        $diff = Invoke-JulesGit -Git $git -Arguments @("diff", "--cached", "--quiet", "--", $gitRelativeDestination) -WorkingDirectory $workspace -AllowFailure
        if ($diff.ExitCode -eq 0) {
            return [pscustomobject]@{
                Status = "already-published"
                ProjectId = $resolvedProjectId
                JobId = $resolvedJobId
                Destination = $repositoryDestination
                GitPath = $gitRelativeDestination
            }
        }
        if ($diff.ExitCode -ne 1) {
            throw "Unable to inspect staged summary changes.`n$($diff.Output)"
        }

        $jobToken = if ($null -eq $resolvedJobId) { "UNASSIGNED" } else { $resolvedJobId }
        $commitMessage = ([string]$config.commit_message_template).Replace("{project_id}", $resolvedProjectId).Replace("{job_id}", $jobToken)

        Invoke-JulesGit -Git $git -Arguments @("commit", "-m", $commitMessage, "--", $gitRelativeDestination) -WorkingDirectory $workspace | Out-Null
        Invoke-JulesGit -Git $git -Arguments @("push", "origin", [string]$config.branch) -WorkingDirectory $workspace | Out-Null

        $commit = Invoke-JulesGit -Git $git -Arguments @("rev-parse", "HEAD") -WorkingDirectory $workspace
        return [pscustomobject]@{
            Status = "published"
            ProjectId = $resolvedProjectId
            JobId = $resolvedJobId
            Destination = $repositoryDestination
            GitPath = $gitRelativeDestination
            Commit = $commit.Output.Trim()
        }
    }
    finally {
        if ($null -ne $lockStream) {
            $lockStream.Dispose()
        }
    }
}

Export-ModuleMember -Function @(
    "Send-AntmuxSummary",
    "Test-AntmuxJulesPublisher"
)
