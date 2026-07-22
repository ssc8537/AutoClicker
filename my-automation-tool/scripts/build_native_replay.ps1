param(
    [ValidateSet("debug", "release")]
    [string]$Profile = "release"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ToolingRoot = "C:\MAPL-Native-Replay"
$VsDevCmd = "C:\MAPL-Native-Replay\vs-buildtools\Common7\Tools\VsDevCmd.bat"
$env:RUSTUP_HOME = Join-Path $ToolingRoot "rustup"
$env:CARGO_HOME = Join-Path $ToolingRoot "cargo"
$env:RUSTUP_DIST_SERVER = "https://rsproxy.cn"
$env:RUSTUP_UPDATE_ROOT = "https://rsproxy.cn/rustup"
$ToolchainBin = Join-Path $env:RUSTUP_HOME "toolchains\stable-x86_64-pc-windows-msvc\bin"
$CargoExe = Join-Path $ToolchainBin "cargo.exe"
$env:RUSTC = Join-Path $ToolchainBin "rustc.exe"
$env:PATH = $ToolchainBin + ";" + $env:PATH

if (-not (Test-Path $VsDevCmd)) {
    throw "Missing MSVC build tools: $VsDevCmd"
}

$temporary = [System.IO.Path]::GetTempFileName() + ".cmd"
try {
    Set-Content -LiteralPath $temporary -Encoding Ascii -Value "@call `"$VsDevCmd`" -arch=amd64 -host_arch=amd64 >nul && set"
    cmd.exe /d /s /c "`"$temporary`"" | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
    $NativeRoot = Join-Path $ProjectRoot "native-replay"
    $arguments = @("build", "--locked")
    if ($Profile -eq "release") {
        $arguments += "--release"
    }
    Push-Location $NativeRoot
    try {
        & $CargoExe @arguments
    } finally {
        Pop-Location
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Cargo build failed: $LASTEXITCODE"
    }
} finally {
    Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
}
