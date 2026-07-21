#requires -Version 5.1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-AntmuxBridgeRoot {
    if (-not [string]::IsNullOrWhiteSpace($env:ANTMUX_ROOT)) {
        return [System.IO.Path]::GetFullPath($env:ANTMUX_ROOT)
    }

    $modulesDirectory = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    return [System.IO.Path]::GetFullPath($modulesDirectory)
}

function Resolve-AntmuxBridgePath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Path
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path $Root $Path))
}

function Get-AntmuxValue {
    param(
        [Parameter(Mandatory = $true)][object]$Object,
        [Parameter(Mandatory = $true)][string[]]$Names
    )

    foreach ($name in $Names) {
        foreach ($property in $Object.PSObject.Properties) {
            if ($property.Name -ieq $name) {
                return $property.Value
            }
        }
    }

    return $null
}

function ConvertTo-AntmuxNullableBoolean {
    param([object]$Value)

    if ($null -eq $Value) {
        return $null
    }

    if ($Value -is [bool]) {
        return [bool]$Value
    }

    $parsed = $false
    if ([bool]::TryParse([string]$Value, [ref]$parsed)) {
        return $parsed
    }

    if ([string]$Value -eq "1") {
        return $true
    }

    if ([string]$Value -eq "0") {
        return $false
    }

    return $null
}

function ConvertTo-AntmuxTileNumber {
    param([object]$Value)

    if ($null -eq $Value) {
        return $null
    }

    $number = 0
    if ([int]::TryParse([string]$Value, [ref]$number) -and $number -gt 0) {
        return $number
    }

    return $null
}

function Find-AntmuxTileCandidate {
    param(
        [object]$Node,
        [int]$Depth = 0,
        [Nullable[int]]$ImplicitTileNumber = $null
    )

    if ($null -eq $Node -or $Depth -gt 24) {
        return
    }

    if ($Node -is [string] -or $Node -is [ValueType]) {
        return
    }

    if ($Node -is [System.Collections.IDictionary]) {
        foreach ($key in $Node.Keys) {
            $nextImplicit = $ImplicitTileNumber
            $numericKey = ConvertTo-AntmuxTileNumber -Value $key
            if ($null -ne $numericKey) {
                $nextImplicit = [Nullable[int]]$numericKey
            }
            Find-AntmuxTileCandidate -Node $Node[$key] -Depth ($Depth + 1) -ImplicitTileNumber $nextImplicit
        }
        return
    }

    if ($Node -is [System.Collections.IEnumerable] -and -not ($Node -is [string])) {
        foreach ($item in $Node) {
            Find-AntmuxTileCandidate -Node $item -Depth ($Depth + 1) -ImplicitTileNumber $ImplicitTileNumber
        }
        return
    }

    $tileNumber = ConvertTo-AntmuxTileNumber -Value (Get-AntmuxValue -Object $Node -Names @(
        "tile_number", "TileNumber", "tileNumber", "tile_id", "TileId", "tile"
    ))
    if ($null -eq $tileNumber -and $ImplicitTileNumber.HasValue) {
        $tileNumber = $ImplicitTileNumber.Value
    }

    $url = Get-AntmuxValue -Object $Node -Names @(
        "url", "Url", "current_url", "CurrentUrl", "tile_url", "TileUrl"
    )

    if ($null -ne $tileNumber -and -not [string]::IsNullOrWhiteSpace([string]$url)) {
        [pscustomobject]@{
            TileNumber = [int]$tileNumber
            Url = [string]$url
            Visible = ConvertTo-AntmuxNullableBoolean -Value (Get-AntmuxValue -Object $Node -Names @(
                "visible", "Visible", "is_visible", "IsVisible"
            ))
            Loaded = ConvertTo-AntmuxNullableBoolean -Value (Get-AntmuxValue -Object $Node -Names @(
                "loaded", "Loaded", "is_loaded", "IsLoaded", "page_loaded", "PageLoaded"
            ))
            PromptFound = ConvertTo-AntmuxNullableBoolean -Value (Get-AntmuxValue -Object $Node -Names @(
                "prompt_found", "PromptFound", "has_prompt", "HasPrompt", "composer_found", "ComposerFound"
            ))
            DisplayDevice = [string](Get-AntmuxValue -Object $Node -Names @(
                "dynamic_screen", "DynamicScreen", "display_device", "DisplayDevice", "screen", "Screen"
            ))
        }
    }

    foreach ($property in $Node.PSObject.Properties) {
        $nextImplicit = $ImplicitTileNumber
        $numericName = ConvertTo-AntmuxTileNumber -Value $property.Name
        if ($null -ne $numericName) {
            $nextImplicit = [Nullable[int]]$numericName
        }
        Find-AntmuxTileCandidate -Node $property.Value -Depth ($Depth + 1) -ImplicitTileNumber $nextImplicit
    }
}

function Write-AntmuxAtomicJson {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][object]$Data
    )

    $directory = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($directory)) {
        New-Item -ItemType Directory -Force -Path $directory | Out-Null
    }

    $temporaryPath = $Path + ".tmp." + [Guid]::NewGuid().ToString("N")
    $json = $Data | ConvertTo-Json -Depth 20
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($temporaryPath, $json + [Environment]::NewLine, $encoding)
    Move-Item -LiteralPath $temporaryPath -Destination $Path -Force
}

function Get-AntmuxBridgeTargetConfig {
    param([string]$ConfigPath)

    $root = Get-AntmuxBridgeRoot
    if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
        $ConfigPath = Join-Path $root "config\chatgpt-bridge-target.json"
    }

    $resolved = Resolve-AntmuxBridgePath -Root $root -Path $ConfigPath
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        throw "TARGET_CONFIGURATION_NOT_FOUND: $resolved"
    }

    $config = Get-Content -LiteralPath $resolved -Raw | ConvertFrom-Json
    $schemaVersion = Get-AntmuxValue -Object $config -Names @("schema_version", "SchemaVersion")
    $enabled = ConvertTo-AntmuxNullableBoolean -Value (Get-AntmuxValue -Object $config -Names @("enabled", "Enabled"))
    $targetType = [string](Get-AntmuxValue -Object $config -Names @("target_type", "TargetType"))
    $tileNumber = ConvertTo-AntmuxTileNumber -Value (Get-AntmuxValue -Object $config -Names @("tile_number", "TileNumber"))
    $allowedPrefixes = @(Get-AntmuxValue -Object $config -Names @("allowed_url_prefixes", "AllowedUrlPrefixes"))

    if ([int]$schemaVersion -ne 1) {
        throw "TARGET_CONFIGURATION_INVALID: schema_version must be 1"
    }
    if ($null -eq $enabled) {
        throw "TARGET_CONFIGURATION_INVALID: enabled must be boolean"
    }
    if ($targetType -ine "nino-tile") {
        throw "TARGET_CONFIGURATION_INVALID: target_type must be nino-tile"
    }
    if ($null -eq $tileNumber) {
        throw "TARGET_CONFIGURATION_INVALID: tile_number must be a positive integer"
    }
    if ($allowedPrefixes.Count -eq 0) {
        throw "TARGET_CONFIGURATION_INVALID: allowed_url_prefixes must not be empty"
    }

    return [pscustomobject]@{
        Path = $resolved
        Data = $config
        Enabled = [bool]$enabled
        TileNumber = [int]$tileNumber
        AllowedUrlPrefixes = @($allowedPrefixes | ForEach-Object { [string]$_ })
        RequireVisible = [bool](ConvertTo-AntmuxNullableBoolean -Value (Get-AntmuxValue -Object $config -Names @("require_visible", "RequireVisible")))
        RequireLoaded = [bool](ConvertTo-AntmuxNullableBoolean -Value (Get-AntmuxValue -Object $config -Names @("require_loaded", "RequireLoaded")))
        RequirePromptElement = [bool](ConvertTo-AntmuxNullableBoolean -Value (Get-AntmuxValue -Object $config -Names @("require_prompt_element", "RequirePromptElement")))
        SelectedBy = [string](Get-AntmuxValue -Object $config -Names @("selected_by", "SelectedBy"))
    }
}

function Get-ChatGPTBridgeTarget {
    [CmdletBinding()]
    param(
        [string]$ConfigPath,
        [string]$NinoSessionPath
    )

    $root = Get-AntmuxBridgeRoot
    $config = Get-AntmuxBridgeTargetConfig -ConfigPath $ConfigPath

    if (-not $config.Enabled) {
        return [pscustomobject]@{
            Status = "TARGET_CONFIGURATION_DISABLED"
            Valid = $false
            ConfigPath = $config.Path
        }
    }

    if ([string]::IsNullOrWhiteSpace($NinoSessionPath)) {
        $NinoSessionPath = Join-Path $root "tools\ninoscreens\data\dashboard_session.json"
    }

    $resolvedSession = Resolve-AntmuxBridgePath -Root $root -Path $NinoSessionPath
    if (-not (Test-Path -LiteralPath $resolvedSession -PathType Leaf)) {
        return [pscustomobject]@{
            Status = "NINO_SESSION_NOT_FOUND"
            Valid = $false
            ConfigPath = $config.Path
            SessionPath = $resolvedSession
            TileNumber = $config.TileNumber
        }
    }

    $session = Get-Content -LiteralPath $resolvedSession -Raw | ConvertFrom-Json
    $allCandidates = @(Find-AntmuxTileCandidate -Node $session)
    $targetMatches = @($allCandidates | Where-Object { $_.TileNumber -eq $config.TileNumber })

    if ($targetMatches.Count -eq 0) {
        return [pscustomobject]@{
            Status = "TARGET_TILE_NOT_FOUND"
            Valid = $false
            ConfigPath = $config.Path
            SessionPath = $resolvedSession
            TileNumber = $config.TileNumber
            CandidateCount = $allCandidates.Count
        }
    }

    if ($targetMatches.Count -gt 1) {
        return [pscustomobject]@{
            Status = "TARGET_TILE_AMBIGUOUS"
            Valid = $false
            ConfigPath = $config.Path
            SessionPath = $resolvedSession
            TileNumber = $config.TileNumber
            MatchCount = $targetMatches.Count
        }
    }

    $target = $targetMatches[0]
    $urlAllowed = $false
    foreach ($prefix in $config.AllowedUrlPrefixes) {
        if ($target.Url.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            $urlAllowed = $true
            break
        }
    }

    $status = "TARGET_RESOLVED_BY_CONFIGURATION"
    $valid = $true
    if (-not $urlAllowed) {
        $status = "TARGET_URL_NOT_ALLOWED"
        $valid = $false
    }
    elseif ($config.RequireVisible -and $target.Visible -ne $true) {
        $status = "TARGET_NOT_VISIBLE"
        $valid = $false
    }
    elseif ($config.RequireLoaded -and $target.Loaded -ne $true) {
        $status = "TARGET_NOT_LOADED"
        $valid = $false
    }
    elseif ($config.RequirePromptElement -and $target.PromptFound -ne $true) {
        $status = "TARGET_PROMPT_NOT_FOUND"
        $valid = $false
    }

    $otherChatGPTTiles = @(
        $allCandidates |
            Where-Object {
                $_.TileNumber -ne $config.TileNumber -and
                $_.Url.StartsWith("https://chatgpt.com/", [System.StringComparison]::OrdinalIgnoreCase)
            } |
            Select-Object -ExpandProperty TileNumber -Unique |
            Sort-Object
    )

    return [pscustomobject]@{
        Status = $status
        Valid = $valid
        ConfigPath = $config.Path
        SessionPath = $resolvedSession
        TileNumber = $target.TileNumber
        TileUrl = $target.Url
        Visible = $target.Visible
        Loaded = $target.Loaded
        PromptFound = $target.PromptFound
        DisplayDevice = $target.DisplayDevice
        SelectedBy = $config.SelectedBy
        OtherChatGPTTiles = $otherChatGPTTiles
    }
}

function Test-ChatGPTBridgeTarget {
    [CmdletBinding()]
    param(
        [string]$ConfigPath,
        [string]$NinoSessionPath
    )

    return Get-ChatGPTBridgeTarget -ConfigPath $ConfigPath -NinoSessionPath $NinoSessionPath
}

function Set-ChatGPTBridgeTarget {
    [CmdletBinding()]
    param(
        [string]$ConfigPath,
        [int]$TileNumber = 1,
        [string[]]$AllowedUrlPrefixes = @("https://chatgpt.com/"),
        [bool]$RequireVisible = $true,
        [bool]$RequireLoaded = $true,
        [bool]$RequirePromptElement = $true,
        [string]$SelectedBy = "Brutus",
        [switch]$Force
    )

    if ($TileNumber -lt 1) {
        throw "TARGET_CONFIGURATION_INVALID: TileNumber must be positive"
    }
    if ($AllowedUrlPrefixes.Count -eq 0) {
        throw "TARGET_CONFIGURATION_INVALID: AllowedUrlPrefixes must not be empty"
    }

    $root = Get-AntmuxBridgeRoot
    if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
        $ConfigPath = Join-Path $root "config\chatgpt-bridge-target.json"
    }
    $resolved = Resolve-AntmuxBridgePath -Root $root -Path $ConfigPath

    if (Test-Path -LiteralPath $resolved -PathType Leaf) {
        if (-not $Force) {
            throw "TARGET_CONFIGURATION_EXISTS: use -Force to replace it"
        }
        $backup = $resolved + ".backup." + (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssfffZ") + ".json"
        Copy-Item -LiteralPath $resolved -Destination $backup
    }

    $data = [ordered]@{
        schema_version = 1
        enabled = $true
        target_type = "nino-tile"
        tile_number = $TileNumber
        allowed_url_prefixes = @($AllowedUrlPrefixes)
        require_visible = $RequireVisible
        require_loaded = $RequireLoaded
        require_prompt_element = $RequirePromptElement
        selected_by = $SelectedBy
    }

    Write-AntmuxAtomicJson -Path $resolved -Data $data
    return [pscustomobject]@{
        Status = "TARGET_CONFIGURATION_WRITTEN"
        ConfigPath = $resolved
        TileNumber = $TileNumber
        SelectedBy = $SelectedBy
    }
}

function Clear-ChatGPTBridgeTarget {
    [CmdletBinding()]
    param([string]$ConfigPath)

    $root = Get-AntmuxBridgeRoot
    if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
        $ConfigPath = Join-Path $root "config\chatgpt-bridge-target.json"
    }
    $resolved = Resolve-AntmuxBridgePath -Root $root -Path $ConfigPath

    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        return [pscustomobject]@{
            Status = "TARGET_CONFIGURATION_ABSENT"
            ConfigPath = $resolved
        }
    }

    $archive = $resolved + ".cleared." + (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssfffZ") + ".json"
    Move-Item -LiteralPath $resolved -Destination $archive
    return [pscustomobject]@{
        Status = "TARGET_CONFIGURATION_CLEARED"
        ConfigPath = $resolved
        ArchivePath = $archive
    }
}

Export-ModuleMember -Function @(
    "Get-ChatGPTBridgeTarget",
    "Test-ChatGPTBridgeTarget",
    "Set-ChatGPTBridgeTarget",
    "Clear-ChatGPTBridgeTarget"
)
