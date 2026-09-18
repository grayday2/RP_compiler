#requires -Version 5.1
# Offline tests: no Pester, downloaded binaries, or network needed.
$ErrorActionPreference = 'Stop'
. (Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts/setup_helpers.ps1')
Add-Type -AssemblyName System.IO.Compression.FileSystem
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('rp2040 setup test ' + [guid]::NewGuid().ToString('N'))
$null = [IO.Directory]::CreateDirectory($testRoot)
$passed = 0
function Assert([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Must-Fail([scriptblock]$Action, [string]$Message) {
    $failed = $false
    try { & $Action } catch { $failed = $true }
    Assert $failed $Message
    $script:passed++
}
try {
    foreach ($bad in @('../outside','..\outside','file:stream','/absolute')) {
        Must-Fail { Get-SafeChildPath $testRoot $bad | Out-Null } ('Accepted unsafe path: ' + $bad)
    }
    $placeholder = Join-Path $testRoot 'placeholder/bin'
    $null = [IO.Directory]::CreateDirectory($placeholder)
    [IO.File]::WriteAllText((Join-Path $placeholder '.gitkeep'), '')
    Assert (Test-EmptyPlaceholder (Join-Path $testRoot 'placeholder')) 'Nested Git placeholders must be accepted'
    $passed++
    $source = Join-Path $testRoot 'source/package'
    $null = [IO.Directory]::CreateDirectory((Join-Path $source 'bin'))
    [IO.File]::WriteAllText((Join-Path $source 'bin/tool.txt'), 'original tool')
    $zip = Join-Path $testRoot 'package.zip'
    [IO.Compression.ZipFile]::CreateFromDirectory((Join-Path $testRoot 'source'), $zip)
    $component = [pscustomobject]@{ id='test'; version='1'; kind='zip'; stripRoot=$true; destination='installed'; sha256=(Get-Sha256 $zip); required=@('bin/tool.txt') }
    $work = Join-Path $testRoot 'work'
    $null = [IO.Directory]::CreateDirectory($work)
    Install-CachedComponent $testRoot $component $zip $work
    Assert (Test-InstalledComponent $testRoot $component) 'Fresh install not detected'
    $passed++
    Install-CachedComponent $testRoot $component $zip $work
    Assert (Test-InstalledComponent $testRoot $component) 'Rerun failed'
    $passed++
    [IO.File]::WriteAllText((Join-Path $testRoot 'installed/bin/tool.txt'), 'modified')
    Assert (-not (Test-InstalledComponent $testRoot $component)) 'Modification was not detected'
    Must-Fail { Install-CachedComponent $testRoot $component $zip $work } 'Overwrote modified installation'
    Assert ([IO.File]::ReadAllText((Join-Path $testRoot 'installed/bin/tool.txt')) -eq 'modified') 'Changed existing file'
    $component.destination = 'wrong-hash'
    $component.sha256 = '0' * 64
    Must-Fail { Install-CachedComponent $testRoot $component $zip $work } 'Accepted wrong hash'
    Assert (-not (Test-Path -LiteralPath (Join-Path $testRoot 'wrong-hash'))) 'Created destination on hash mismatch'
    $component.sha256 = Get-Sha256 $zip
    $component.destination = 'incomplete'
    $component.required = @('missing.txt')
    Must-Fail { Install-CachedComponent $testRoot $component $zip $work } 'Accepted incomplete archive'
    Assert (-not (Test-Path -LiteralPath (Join-Path $testRoot 'incomplete'))) 'Published incomplete archive'
    # Deliberately hostile ZIP traversal must be rejected before extraction.
    $evil = Join-Path $testRoot 'evil.zip'
    $z = [IO.Compression.ZipFile]::Open($evil, [IO.Compression.ZipArchiveMode]::Create)
    $null = $z.CreateEntry('../outside.txt')
    $z.Dispose()
    Must-Fail { Expand-CheckedZip $evil (Join-Path $testRoot 'evil-out') } 'ZIP traversal accepted'
    Assert (-not (Test-Path -LiteralPath (Join-Path $testRoot 'outside.txt'))) 'ZIP escaped extraction directory'
    # A raw pinned file can be installed and recognized, but not silently replaced.
    $raw = [pscustomobject]@{id='raw';version='1';kind='file';stripRoot=$false;destination='raw/tool.txt';sha256=(Get-Sha256 (Join-Path $source 'bin/tool.txt'));required=@()}
    Install-CachedComponent $testRoot $raw (Join-Path $source 'bin/tool.txt') $work
    Assert (Test-InstalledComponent $testRoot $raw) 'Raw file installation failed'
    $passed++
    # Enter is conservative; y is the only interactive cleanup choice.
    Assert (-not (Confirm-SetupCacheCleanup -ReadAnswer { param($text) '' })) 'Enter must keep cache'
    Assert (Confirm-SetupCacheCleanup -ReadAnswer { param($text) ' y ' }) 'y must select cleanup'
    Assert (Confirm-SetupCacheCleanup -ReadAnswer { param($text) 'Y' }) 'Uppercase Y must select cleanup'
    Assert (-not (Confirm-SetupCacheCleanup -ReadAnswer { param($text) 'yes' })) 'Other answers must keep cache'
    Assert (-not (Confirm-SetupCacheCleanup -NoPrompt -ReadAnswer { throw 'Unexpected prompt' })) 'NoPrompt must keep cache'
    Assert (Confirm-SetupCacheCleanup -CleanupCache -NoPrompt -ReadAnswer { throw 'Unexpected prompt' }) 'CleanupCache must work without prompt'
    $passed += 6
    # Only disposable setup paths may be removed, even if other directories are present.
    foreach ($name in @('.setup-cache', '.setup-work', 'cmake', 'toolchain', 'python', 'pico-sdk', 'output', 'debug/logs')) {
        $dir = Join-Path $testRoot $name
        $null = [IO.Directory]::CreateDirectory($dir)
        [IO.File]::WriteAllText((Join-Path $dir 'keep.txt'), $name)
    }
    Remove-SetupCache $testRoot
    foreach ($name in @('.setup-cache', '.setup-work')) {
        Assert (-not (Test-Path -LiteralPath (Join-Path $testRoot $name))) 'Setup cache was not removed'
    }
    foreach ($name in @('cmake', 'toolchain', 'python', 'pico-sdk', 'output', 'debug/logs')) {
        Assert (Test-Path -LiteralPath (Join-Path $testRoot ($name + '/keep.txt'))) 'Cleanup touched an installed component or output'
    }
    Remove-SetupCache $testRoot # already absent is harmless
    $passed++
    if ($env:OS -eq 'Windows_NT') {
        $cacheDir = Join-Path $testRoot '.setup-cache'
        $null = [IO.Directory]::CreateDirectory($cacheDir)
        $junction = Join-Path $cacheDir 'linked-tools'
        $null = New-Item -ItemType Junction -Path $junction -Target (Join-Path $testRoot 'toolchain')
        try {
            Must-Fail { Remove-SetupCache $testRoot } 'Cleanup traversed a junction'
            Assert (Test-Path -LiteralPath (Join-Path $testRoot 'toolchain/keep.txt')) 'Cleanup touched junction target'
        } finally { [IO.Directory]::Delete($junction) }
    }
    Write-Host "PASS: $passed offline installer checks"
} finally {
    Remove-Item -LiteralPath $testRoot -Recurse -Force
}
