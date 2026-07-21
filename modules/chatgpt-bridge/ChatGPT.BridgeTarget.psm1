#requires -Version 5.1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-AntmuxBridgeRoot {
    if (-not [string]::IsNullOrWhiteSpace($env:ANTMUX_ROOT)) {
        return [System.IO.Path]::GetFullPath($env:ANTMUX_ROOT)
    }

    return [System.IO.Path]::GetFullPath((Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
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

function Get-AntmuxPropertyValue {
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

function ConvertTo-AntmuxBoolean {
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

function ConvertTo-AntmuxPositiveInteger {
    param([object]$Value)

    if ($null -eq $Value) {
        return $null
    }

    $parsed = 0
    if ([int]::TryParse([string]$Value, [ref]$parsed) -and $parsed -gt 0) {
        return $parsed
    }

    return $null
}

function Find-AntmuxNinoTile {
    param(
        [object]$Node,
        [int]$Depth = 0,
        [int]$ImplicitTileNumber = 0
    )

    if ($null -eq $Node -or $Depth -gt 24) {
        return
    }
    if ($Node -is [string] -or $Node -is [ValueType]) {
        return
    }

    if ($Node -is [System.Collections.IDictionary]) {
        foreach ($key in $Node.Keys) {
            $nextTileNumber = $ImplicitTileNumber
            $numericKey = ConvertTo-AntmuxPositiveInteger -Value $key
            if ($null -ne $numericKey) {
                $nextTileNumber = [int]$numericKey
            }
            Find-AntmuxNinoTile -Node $Node[$key] -Depth ($Depth + 1) -ImplicitTileNumber $nextTileNumber
        }
        return
    }

    if ($Node -is [System.Collections.IEnumerable] -and -not ($Node -is [string])) {
        foreach ($item in $Node) {
            Find-AntmuxNinoTile -Node $item -Depth ($Depth + 1) -ImplicitTileNumber $ImplicitTileNumber
        }
        return
    }

    $tileNumber = ConvertTo-AntmuxPositiveInteger -Value (Get-AntmuxPropertyValue -Object $Node -Names @(
        "tile_number", "TileNumber", "tileNumber", "tile_id", "TileId", "tile"
    ))
    if ($null -eq $tileNumber -and $ImplicitTileNumber -gt 0) {
        $tileNumber = $ImplicitTileNumber
    }

    $url = Get-AntmuxPropertyValue -Object $Node -Names @(
        "url", "Url", "current_url", "CurrentUrl", "tile_url", "TileUrl"
    )

    if ($null -ne $tileNumber -and -not [string]::IsNullOrWhiteSpace([string]$url)) {
        [pscustomobject]@{
            TileNumber = [int]$tileNumber
            Url = [string]$url
            Visible = ConvertTo-AntmuxBoolean -Value (Get-AntmuxPropertyValue -Object $Node -Names @(
                "visible", "Visible", "is_visible", "IsVisible"
            ))
            Loaded = ConvertTo-AntmuxBoolean -Value (Get-AntmuxPropertyValue -Object $Node -Names @(
                "loaded", "Loaded", "is_loaded", "IsLoaded", "page_loaded", "PageLoaded"
            ))
            PromptFound = ConvertTo-AntmuxBoolean -Value (Get-AntmuxPropertyValue -Object $Node -Names @(
                "prompt_found", "PromptFound", "has_prompt", "HasPrompt", "composer_found", "ComposerFound"
            ))
            DisplayDevice = [string](Get-AntmuxPropertyValue -Object $Node -Names @(
                "dynamic_screen", "DynamicScreen", "display_device", "DisplayDevice", "screen", "Screen"
            ))
        }
    }

    foreach ($property in $Node.PSObject.Properties) {
        $nextTileNumber = $ImplicitTileNumber
        $numericName = ConvertTo-AntmuxPositiveInteger -Value $property.Name
        if ($null -ne $numericName) {
            $nextTileNumber = [int]$numericName
        }
        Find-AntmuxNinoTile -Node $property.Value -Depth ($Depth + 1) -ImplicitTileNumber $nextTileNumber
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

    $resolvedPath = Resolve-AntmuxBridgePath -Root $root -Path $ConfigPath
    if (-not (Test-Path -LiteralPath $resolvedPath -PathType Leaf)) {
        throw "TARGET_CONFIGURATION_NOT_FOUND: $resolvedPath"
    }

    $data = Get-Content -LiteralPath $resolvedPath -Raw | ConvertFrom-Json
    $schemaVersion = ConvertTo-AntmuxPositiveInteger -Value (Get-AntmuxPropertyValue -Object $data -Names @("schema_version", "SchemaVersion"))
    $enabled = ConvertTo-AntmuxBoolean -Value (Get-AntmuxPropertyValue -Object $data -Names @("enabled", "Enabled"))
    $targetType = [string](Get-AntmuxPropertyValue -Object $data -Names @("target_type", "TargetType"))
    $tileNumber = ConvertTo-AntmuxPositiveInteger -Value (Get-AntmuxPropertyValue -Object $data -Names @("tile_number", "TileNumber"))
    $allowedPrefixes = @(Get-AntmuxPropertyValue -Object $data -Names @("allowed_url_prefixes", "AllowedUrlPrefixes"))

    if ($schemaVersion -ne 1) {
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

    $requireVisible = ConvertTo-AntmuxBoolean -Value (Get-AntmuxPropertyValue -Object $data -Names @("require_visible", "RequireVisible"))
    $requireLoaded = ConvertTo-AntmuxBoolean -Value (Get-AntmuxPropertyValue -Object $data -Names @("require_loaded", "RequireLoaded"))
    $requirePrompt = ConvertTo-AntmuxBoolean -Value (Get-AntmuxPropertyValue -Object $data -Names @("require_prompt_element", "RequirePromptElement"))

    return [pscustomobject]@{
        Path = $resolvedPath
        Enabled = [bool]$enabled
        TileNumber = [int]$tileNumber
        AllowedUrlPrefixes = @($allowedPrefixes | ForEach-Object { [string]$_ })
        RequireVisible = if ($null -eq $requireVisible) { $false } else { [bool]$requireVisible }
        RequireLoaded = if ($null -eq $requireLoaded) { $false } else { [bool]$requireLoaded }
        RequirePromptElement = if ($null -eq $requirePrompt) { $false } else { [bool]$requirePrompt }
        SelectedBy = [string](Get-AntmuxPropertyValue -Object $data -Names @("selected_by", "SelectedBy"))
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

    $resolvedSessionPath = Resolve-AntmuxBridgePath -Root $root -Path $NinoSessionPath
    if (-not (Test-Path -LiteralPath $resolvedSessionPath -PathType Leaf)) {
        return [pscustomobject]@{
            Status = "NINO_SESSION_NOT_FOUND"
            Valid = $false
            ConfigPath = $config.Path
            SessionPath = $resolvedSessionPath
            TileNumber = $config.TileNumber
        }
    }

    $session = Get-Content -LiteralPath $resolvedSessionPath -Raw | ConvertFrom-Json
    $candidates = @(Find-AntmuxNinoTile -Node $session)
    $matches = @($candidates | Where-Object { $_.TileNumber -eq $config.TileNumber })

    if ($matches.Count -eq 0) {
        return [pscustomobject]@{
            Status = "TARGET_TILE_NOT_FOUND"
            Valid = $false
            ConfigPath = $config.Path
            SessionPath = $resolvedSessionPath
            TileNumber = $config.TileNumber
            CandidateCount = $candidates.Count
        }
    }
    if ($matches.Count -gt 1) {
        return [pscustomobject]@{
            Status = "TARGET_TILE_AMBIGUOUS"
            Valid = $false
            ConfigPath = $config.Path
            SessionPath = $resolvedSessionPath
            TileNumber = $config.TileNumber
            MatchCount = $matches.Count
        }
    }

    $target = $matches[0]
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
        $candidates |
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
        SessionPath = $resolvedSessionPath
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
    $resolvedPath = Resolve-AntmuxBridgePath -Root $root -Path $ConfigPath

    if (Test-Path -LiteralPath $resolvedPath -PathType Leaf) {
        if (-not $Force) {
            throw "TARGET_CONFIGURATION_EXISTS: use -Force to replace it"
        }
        $backupPath = $resolvedPath + ".backup." + (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssfffZ") + ".json"
        Copy-Item -LiteralPath $resolvedPath -Destination $backupPath
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

    Write-AntmuxAtomicJson -Path $resolvedPath -Data $data
    return [pscustomobject]@{
        Status = "TARGET_CONFIGURATION_WRITTEN"
        ConfigPath = $resolvedPath
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
    $resolvedPath = Resolve-AntmuxBridgePath -Root $root -Path $ConfigPath

    if (-not (Test-Path -LiteralPath $resolvedPath -PathType Leaf)) {
        return [pscustomobject]@{
            Status = "TARGET_CONFIGURATION_ABSENT"
            ConfigPath = $resolvedPath
        }
    }

    $archivePath = $resolvedPath + ".cleared." + (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssfffZ") + ".json"
    Move-Item -LiteralPath $resolvedPath -Destination $archivePath
    return [pscustomobject]@{
        Status = "TARGET_CONFIGURATION_CLEARED"
        ConfigPath = $resolvedPath
        ArchivePath = $archivePath
    }
}

Export-ModuleMember -Function @(
    "Get-ChatGPTBridgeTarget",
    "Test-ChatGPTBridgeTarget",
    "Set-ChatGPTBridgeTarget",
    "Clear-ChatGPTBridgeTarget"
)
