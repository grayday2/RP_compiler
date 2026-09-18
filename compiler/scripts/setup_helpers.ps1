# Pure helpers shared by first_setup.ps1 and the offline installer tests.
Set-StrictMode -Version Latest

function Get-Sha256([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
}
function Test-ArchiveHash([string]$Path, [string]$Expected) {
    (Test-Path -LiteralPath $Path -PathType Leaf) -and ((Get-Sha256 $Path) -eq $Expected.ToLowerInvariant())
}
function Get-SafeChildPath([string]$Base, [string]$Relative) {
    if ([string]::IsNullOrWhiteSpace($Relative) -or [IO.Path]::IsPathRooted($Relative) -or $Relative.Contains(':')) {
        throw "Invalid relative path: $Relative"
    }
    $baseFull = [IO.Path]::GetFullPath($Base).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    $relativeNative = $Relative.Replace('\', [IO.Path]::DirectorySeparatorChar).Replace('/', [IO.Path]::DirectorySeparatorChar)
    $full = [IO.Path]::GetFullPath((Join-Path $baseFull $relativeNative))
    if (-not $full.StartsWith($baseFull, [StringComparison]::OrdinalIgnoreCase)) { throw "Path escapes destination: $Relative" }
    return $full
}
function Expand-CheckedZip([string]$Archive, [string]$Destination) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $null = [IO.Directory]::CreateDirectory($Destination)
    $zip = [IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        # Validate all paths before extracting anything, including Windows ADS paths.
        foreach ($entry in $zip.Entries) {
            $null = Get-SafeChildPath $Destination $entry.FullName
        }
        foreach ($entry in $zip.Entries) {
            $target = Get-SafeChildPath $Destination $entry.FullName
            if ($entry.FullName.EndsWith('/') -or $entry.FullName.EndsWith('\')) {
                $null = [IO.Directory]::CreateDirectory($target)
            } else {
                $null = [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target))
                [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $target, $false)
            }
        }
    } finally { $zip.Dispose() }
}
function Assert-RequiredFiles([string]$Directory, $Required) {
    foreach ($relative in $Required) {
        $path = Get-SafeChildPath $Directory $relative
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing required file: $path" }
    }
}
function Test-EmptyPlaceholder([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $true }
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return $false }
    if ((Get-Item -LiteralPath $Path).Attributes -band [IO.FileAttributes]::ReparsePoint) { return $false }
    foreach ($entry in Get-ChildItem -LiteralPath $Path -Force) {
        if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { return $false }
        if ($entry.PSIsContainer) {
            if (-not (Test-EmptyPlaceholder $entry.FullName)) { return $false }
        } elseif ($entry.Name -ne '.gitkeep') { return $false }
    }
    return $true
}
function Test-InstalledComponent([string]$Root, $Component) {
    $destination = Get-SafeChildPath $Root $Component.destination
    if ($Component.kind -eq 'file') { return Test-ArchiveHash $destination $Component.sha256 }
    $marker = Join-Path $destination '.rp2040-component.json'
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) { return $false }
    try {
        $record = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
        if ($record.id -ne $Component.id -or $record.archiveSha256 -ne $Component.sha256) { return $false }
        Assert-RequiredFiles $destination $Component.required
        foreach ($relative in $Component.required) {
            $property = $record.files.PSObject.Properties[$relative]
            if ($null -eq $property -or (Get-Sha256 (Get-SafeChildPath $destination $relative)) -ne $property.Value) { return $false }
        }
        return $true
    } catch { return $false }
}
function Install-CachedComponent([string]$Root, $Component, [string]$Archive, [string]$Work) {
    if (Test-InstalledComponent $Root $Component) { return }
    if (-not (Test-ArchiveHash $Archive $Component.sha256)) { throw "SHA-256 mismatch: $Archive" }
    $destination = Get-SafeChildPath $Root $Component.destination
    if ($Component.kind -eq 'file') {
        if (Test-Path -LiteralPath $destination) { throw "Refusing to overwrite existing file: $destination" }
        $null = [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination))
        $temp = $destination + '.installing'
        try {
            Copy-Item -LiteralPath $Archive -Destination $temp -ErrorAction Stop
            [IO.File]::Move($temp, $destination)
        } finally { if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force } }
        return
    }
    if (-not (Test-EmptyPlaceholder $destination)) { throw "Refusing to overwrite unmanaged or modified directory: $destination. Use a new project folder." }
    $stage = Get-SafeChildPath $Work $Component.id
    try {
        if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
        Expand-CheckedZip $Archive $stage
        $source = $stage
        if ($Component.stripRoot) {
            $children = @(Get-ChildItem -LiteralPath $stage -Force)
            if ($children.Count -ne 1 -or -not $children[0].PSIsContainer) { throw "Expected exactly one root folder in $Archive" }
            $source = $children[0].FullName
        }
        Assert-RequiredFiles $source $Component.required
        $files = [ordered]@{}
        foreach ($relative in $Component.required) { $files[$relative] = Get-Sha256 (Get-SafeChildPath $source $relative) }
        [ordered]@{id=$Component.id; version=$Component.version; archiveSha256=$Component.sha256; files=$files} |
            ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $source '.rp2040-component.json') -Encoding UTF8
        # Remove only an empty directory or a .gitkeep placeholder, never an old installation.
        if (Test-Path -LiteralPath $destination) {
            if (-not (Test-EmptyPlaceholder $destination)) { throw "Destination changed during installation: $destination" }
            Remove-Item -LiteralPath $destination -Recurse -Force
        }
        $null = [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination))
        [IO.Directory]::Move($source, $destination)
    } finally {
        if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
    }
}
function Invoke-CheckedTool([string]$Executable, [string[]]$Arguments) {
    & $Executable @Arguments | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Tool failed (exit $LASTEXITCODE): $Executable" }
}

function Confirm-SetupCacheCleanup(
    [switch]$NoPrompt,
    [switch]$CleanupCache,
    [scriptblock]$ReadAnswer = { param($PromptText) Read-Host $PromptText }
) {
    if ($CleanupCache) { return $true }
    if ($NoPrompt) { return $false }
    Write-Host ''
    Write-Host 'Setup is complete. Installed tools and firmware will be kept.' -ForegroundColor Green
    $answer = & $ReadAnswer 'Enter = finish and KEEP download cache; y + Enter = DELETE download cache and temporary extraction'
    return ([string]$answer).Trim() -ieq 'y'
}
function Assert-NoCleanupLinks([string]$Directory) {
    $item = Get-Item -LiteralPath $Directory -Force -ErrorAction Stop
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Cleanup refuses a linked path: $Directory" }
    if (-not $item.PSIsContainer) { throw "Cleanup expected a directory: $Directory" }
    foreach ($child in Get-ChildItem -LiteralPath $Directory -Force -ErrorAction Stop) {
        if ($child.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Cleanup refuses a linked path: $($child.FullName)" }
        if ($child.PSIsContainer) { Assert-NoCleanupLinks $child.FullName }
    }
}
function Remove-SetupCache([string]$Root) {
    # This fixed allowlist deliberately excludes tools, build, output, logs and sources.
    $paths = @('.setup-cache', '.setup-work') | ForEach-Object { Get-SafeChildPath $Root $_ }
    # Check both trees before deleting either; never traverse junctions or symlinks.
    foreach ($path in $paths) {
        if (Test-Path -LiteralPath $path) { Assert-NoCleanupLinks $path }
    }
    foreach ($path in $paths) {
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction Stop
            Write-Host ('Removed setup files: ' + $path)
        }
    }
}
