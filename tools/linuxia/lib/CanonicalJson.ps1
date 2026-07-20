Set-StrictMode -Version 2.0

function ConvertTo-LinuxIACanonicalValue {
    param($Value)
    if($null -eq $Value){return $null}
    if($Value -is [string]){return $Value.Normalize([Text.NormalizationForm]::FormC)}
    if($Value -is [bool] -or $Value -is [ValueType]){return $Value}
    if($Value -is [System.Collections.IDictionary]){
        $ordered=[ordered]@{}
        foreach($key in @($Value.Keys | ForEach-Object {[string]$_} | Sort-Object)){
            $ordered[$key]=ConvertTo-LinuxIACanonicalValue $Value[$key]
        }
        return $ordered
    }
    if($Value -is [pscustomobject]){
        $ordered=[ordered]@{}
        foreach($prop in @($Value.PSObject.Properties | Sort-Object Name)){
            $ordered[$prop.Name]=ConvertTo-LinuxIACanonicalValue $prop.Value
        }
        return $ordered
    }
    if($Value -is [System.Collections.IEnumerable]){
        $items=New-Object System.Collections.ArrayList
        foreach($item in $Value){$null=$items.Add((ConvertTo-LinuxIACanonicalValue $item))}
        return ,@($items)
    }
    return ([string]$Value).Normalize([Text.NormalizationForm]::FormC)
}

function ConvertTo-LinuxIACanonicalJson {
    param($Value)
    $canonical=ConvertTo-LinuxIACanonicalValue $Value
    return (($canonical | ConvertTo-Json -Depth 32 -Compress) -replace "`r`n?","`n").Normalize([Text.NormalizationForm]::FormC)
}

function Get-LinuxIAStringSha256 {
    param([string]$Value)
    $encoding=New-Object Text.UTF8Encoding($false)
    $bytes=$encoding.GetBytes($Value.Normalize([Text.NormalizationForm]::FormC))
    $sha=[Security.Cryptography.SHA256]::Create()
    try{$hash=$sha.ComputeHash($bytes)}finally{$sha.Dispose()}
    return 'sha256:' + (($hash | ForEach-Object {$_.ToString('x2')}) -join '')
}

function Get-LinuxIAObjectSha256 {
    param($Value,[string]$ExcludeTopLevelProperty='')
    $copy=[ordered]@{}
    foreach($prop in @($Value.PSObject.Properties | Sort-Object Name)){
        if($prop.Name -ne $ExcludeTopLevelProperty){$copy[$prop.Name]=$prop.Value}
    }
    return Get-LinuxIAStringSha256 (ConvertTo-LinuxIACanonicalJson $copy)
}

function Get-LinuxIACanonicalFileSha256 {
    param([string]$Path)
    $bytes=[IO.File]::ReadAllBytes($Path)
    $text=(New-Object Text.UTF8Encoding($false,$true)).GetString($bytes)
    if($text.Length -gt 0 -and [int][char]$text[0] -eq 0xFEFF){$text=$text.Substring(1)}
    $text=($text -replace "`r`n?","`n").Normalize([Text.NormalizationForm]::FormC)
    return (Get-LinuxIAStringSha256 $text).Substring(7)
}
