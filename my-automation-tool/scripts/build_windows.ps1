param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    python scripts/generate_windows_icon.py
    $pyInstallerArgs = @(
        "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
        "--name", "MyAutoPlayer", "--icon", "assets\myautoplayer-pink.ico",
        "--add-data", "assets;assets", "main.py"
    )
    & python @pyInstallerArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $releaseRoot = Join-Path $projectRoot "dist\MyAutoPlayer"
    Copy-Item -LiteralPath "config" -Destination (Join-Path $releaseRoot "config") -Recurse -Force
    Copy-Item -LiteralPath "macros" -Destination (Join-Path $releaseRoot "macros") -Recurse -Force
    New-Item -ItemType Directory -Path (Join-Path $releaseRoot "logs") -Force | Out-Null
    Write-Host "Portable build: $releaseRoot\MyAutoPlayer.exe"
}
finally {
    Pop-Location
}
