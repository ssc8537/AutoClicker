param(
    [string]$ReleaseName = "MyAutoPlayer",
    [string]$DistPath = "dist"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath "assets\myautoplayer-pink.ico")) {
        throw "缺少用户 EXE/窗口/任务栏图标：assets\myautoplayer-pink.ico"
    }
    if (-not (Test-Path -LiteralPath "assets\myautoplayer-tray.ico")) {
        throw "缺少用户托盘图标：assets\myautoplayer-tray.ico"
    }
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
