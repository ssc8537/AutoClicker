param(
    [string]$ReleaseName = "MyAutoPlayer",
    [string]$DistPath = "dist"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath "assets\myautoplayer.ico")) {
        throw "缺少统一的用户角色图标：assets\myautoplayer.ico"
    }
    python scripts/generate_sound_effects.py
    $workPath = Join-Path $projectRoot ("build\" + $ReleaseName)
    $iconPath = Join-Path $projectRoot "assets\myautoplayer.ico"
    $assetData = (Join-Path $projectRoot "assets") + ";assets"
    $pyInstallerArgs = @(
        "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--uac-admin",
        "--name", $ReleaseName, "--distpath", $DistPath, "--workpath", $workPath,
        "--specpath", $workPath, "--optimize", "1", "--icon", $iconPath,
        "--add-data", $assetData, "main.py"
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
