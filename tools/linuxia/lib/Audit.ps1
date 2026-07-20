Set-StrictMode -Version 2.0

function Write-LinuxIAImmutableJson {
    param([string]$Path,$Value)
    $directory=Split-Path -Parent $Path
    $null=[IO.Directory]::CreateDirectory($directory)
    $encoding=New-Object Text.UTF8Encoding($false)
    $payload=(ConvertTo-LinuxIACanonicalJson $Value)+"`n"
    $stream=New-Object IO.FileStream($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    try{
        $bytes=$encoding.GetBytes($payload)
        $stream.Write($bytes,0,$bytes.Length)
        $stream.Flush($true)
    }finally{$stream.Dispose()}
}

function Add-LinuxIAAuditEvent {
    param([string]$Path,$Value)
    $directory=Split-Path -Parent $Path
    $null=[IO.Directory]::CreateDirectory($directory)
    $encoding=New-Object Text.UTF8Encoding($false)
    $payload=(ConvertTo-LinuxIACanonicalJson $Value)+"`n"
    $stream=New-Object IO.FileStream($Path,[IO.FileMode]::Append,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    try{
        $bytes=$encoding.GetBytes($payload)
        $stream.Write($bytes,0,$bytes.Length)
        $stream.Flush($true)
    }finally{$stream.Dispose()}
}
