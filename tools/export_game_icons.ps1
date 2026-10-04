# Exports game icons to PNG outside the repo. For GOG picks the game EXE instead of
# the round launcher icon; for Steam keeps the shortcut icon. Never launches games.
param(
    [string]$OutDir = (Join-Path $env:TEMP 'notgeese-game-icons'),
    [string]$Game,
    [string]$Executable
)
$ErrorActionPreference = 'Stop'
$repoDir = Split-Path $PSScriptRoot -Parent
if ($Executable -and !$Game) { throw 'Executable requires Game.' }
if ($Game -and !(Test-Path -LiteralPath (Join-Path $repoDir "games/$Game/game.yaml"))) {
    throw "Unknown game: $Game"
}
if ($Executable -and !(Test-Path -LiteralPath $Executable -PathType Leaf)) {
    throw "Executable not found: $Executable"
}
$resolvedOutput = [IO.Path]::GetFullPath($OutDir)
if ($resolvedOutput.StartsWith($repoDir + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or $resolvedOutput -eq $repoDir) {
    throw 'Ikony zapisujemy poza repozytorium. Wybierz inny OutDir.'
}
New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class GameIconNative {
    [DllImport("user32.dll", CharSet=CharSet.Unicode)]
    public static extern uint PrivateExtractIcons(string file, int index, int width, int height,
        IntPtr[] icons, uint[] ids, uint count, uint flags);
    [DllImport("user32.dll")]
    public static extern bool DestroyIcon(IntPtr icon);
}
'@
function Normalize-GameName([string]$name) { return ($name.ToLowerInvariant() -replace '[^a-z0-9]', '') }
$shell = New-Object -ComObject WScript.Shell
$shortcuts = @{}
foreach ($desktop in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('CommonDesktopDirectory'))) {
    foreach ($file in Get-ChildItem -LiteralPath $desktop -File | Where-Object Extension -In '.lnk', '.url') {
        $source = ''; $index = 0
        if ($file.Extension -eq '.lnk') {
            $shortcut = $shell.CreateShortcut($file.FullName)
            $parts = $shortcut.IconLocation -split ',(?=-?\d+$)'
            $source = $parts[0].Trim('"')
            if ($parts.Length -gt 1) { $index = [int]$parts[1] }
            if (!$source) { $source = $shortcut.TargetPath }
        } else {
            $line = Get-Content -LiteralPath $file.FullName | Where-Object { $_ -match '^IconFile=' } | Select-Object -First 1
            if ($line) { $source = $line.Substring(9) }
        }
        if ($source -and (Test-Path -LiteralPath $source)) {
            # Labyrinth: Unreal logo. SPRAWL: a different mark instead of the character icon.
            # For these two games we keep the recognizable GOG icons.
            if ([IO.Path]::GetFileName($source) -match '^goggame-\d+\.(ico|dll)$' -and
                [IO.Path]::GetFileNameWithoutExtension($source) -notin @('goggame-1097598185', 'goggame-1816713701')) {
                $infoPath = [IO.Path]::ChangeExtension($source, '.info')
                if (Test-Path -LiteralPath $infoPath) {
                    $info = Get-Content -LiteralPath $infoPath -Raw | ConvertFrom-Json
                    $task = $info.playTasks | Where-Object { $_.isPrimary -and $_.type -eq 'FileTask' } | Select-Object -First 1
                    if ($task.path) {
                        $gameExecutable = Join-Path (Split-Path $source -Parent) $task.path
                        if (Test-Path -LiteralPath $gameExecutable) { $source = $gameExecutable; $index = 0 }
                    }
                }
            }
            $shortcuts[(Normalize-GameName $file.BaseName)] = @{ Source = $source; Index = $index }
        }
    }
}
foreach ($gameDir in Get-ChildItem (Join-Path $repoDir 'games') -Directory) {
    if ($Game -and $gameDir.Name -ne $Game) { continue }
    if (!(Test-Path (Join-Path $gameDir.FullName 'game.yaml'))) { continue }
    $name = Normalize-GameName $gameDir.Name
    if ($gameDir.Name -eq 'bpm') { $name = 'bpmbulletsperminute' }
    if ($gameDir.Name -eq 'hong-kong-massacre') { $name = 'thehongkongmassacre' }
    $source = $shortcuts[$name]
    if ($Executable) { $source = @{ Source = (Resolve-Path -LiteralPath $Executable).Path; Index = 0 } }
    if (!$source) { Write-Warning "No shortcut: $($gameDir.Name)"; continue }
    $handles = New-Object IntPtr[] 1
    $ids = New-Object uint32[] 1
    $result = [GameIconNative]::PrivateExtractIcons($source.Source, $source.Index, 128, 128, $handles, $ids, 1, 0)
    if ($result -ne 1 -or $handles[0] -eq [IntPtr]::Zero) { throw "Could not extract icon: $($gameDir.Name)" }
    $image = $null; $bitmap = $null
    try {
        $image = [Drawing.Icon]::FromHandle($handles[0])
        $bitmap = $image.ToBitmap()
        $bitmap.Save((Join-Path $resolvedOutput ($gameDir.Name + '.png')), [Drawing.Imaging.ImageFormat]::Png)
        Write-Output "$($gameDir.Name): $($bitmap.Width)x$($bitmap.Height) — $($source.Source)"
    } finally {
        if ($bitmap) { $bitmap.Dispose() }
        if ($image) { $image.Dispose() }
        [GameIconNative]::DestroyIcon($handles[0]) | Out-Null
    }
}
