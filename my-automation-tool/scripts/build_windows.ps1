param(
    [string]$ReleaseName = "MyAutoPlayer",
    [string]$DistPath = "dist"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    python scripts/generate_windows_icon.py
    python scripts/generate_sound_effects.py
    $pyInstallerArgs = @(
        "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
        "--name", $ReleaseName, "--distpath", $DistPath, "--workpath", ("build\" + $ReleaseName), "--icon", "assets\myautoplayer-pink.ico",
        "--add-data", "assets;assets", "main.py"
    )
    & python @pyInstallerArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $releaseRoot = Join-Path $projectRoot (Join-Path $DistPath $ReleaseName)
    Copy-Item -LiteralPath "config" -Destination (Join-Path $releaseRoot "config") -Recurse -Force
    Copy-Item -LiteralPath "macros" -Destination (Join-Path $releaseRoot "macros") -Recurse -Force
    New-Item -ItemType Directory -Path (Join-Path $releaseRoot "logs") -Force | Out-Null
    Write-Host "Portable build: $releaseRoot\$ReleaseName.exe"
}
finally {
    Pop-Location
}
