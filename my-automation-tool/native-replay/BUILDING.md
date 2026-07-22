# 原生录像构建环境

> 本文只供开发者重新编译源码。普通用户录像时不要双击 `.ps1`；Windows 把它打开到记事本也不是故障。请直接运行 `dist\MyAutoPlayer\MyAutoPlayer.exe`，主程序会自动启动随包原生核心。

## 固定路径

- 下载缓存：`<仓库目录>\my-automation-tool\.tooling\native-replay\downloads\`
- Rust 安装器：上述目录的 `rustup-init-x86_64-pc-windows-msvc.exe`
- Visual Studio Build Tools 安装器：上述目录的 `vs_BuildTools-17.exe`
- Rust/Cargo：`C:\MAPL-Native-Replay\rustup\`、`C:\MAPL-Native-Replay\cargo\`
- MSVC/Windows SDK：`C:\MAPL-Native-Replay\vs-buildtools\`

没有修改系统永久 `PATH`。构建脚本只为当前 PowerShell 子进程装载这些路径。
项目内`.cargo/config.toml`属于开发者本机网络镜像设置，已被Git忽略，不是源码依赖。

## 构建

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_native_replay.ps1 -Profile release
```

输出：`native-replay\target\release\myautoplayer-native-replay.exe`。

正式程序构建会先调用上述脚本，再把原生进程复制到 `dist\MyAutoPlayer\native-replay\`。

## 不再需要时清理

先关闭 MyAutoPlayer 和所有构建命令。建议先用 Visual Studio Installer 卸载已注册的 Build Tools：

```powershell
& 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe' uninstall --installPath 'C:\MAPL-Native-Replay\vs-buildtools' --quiet --wait
```

随后可以删除整个 `C:\MAPL-Native-Replay\`，以及项目内被 `.gitignore` 排除的 `.tooling\native-replay\` 下载缓存。删除这些工具不会删除源码、用户宏、配置、日志或已经录好的视频；只会让未来无法重新编译原生组件，直到再次安装。
