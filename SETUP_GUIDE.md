# 环境配置说明（人类与 AI 共用）

本文是下载 MyAutoPlayer 后的唯一环境配置入口。命令面向 Windows 11 PowerShell；人类可以逐条复制，AI 可以按“AI 执行协议”直接配置并验证。

## 1. 已确认的项目事实

| 项目 | 值 |
|---|---|
| 仓库 | `https://github.com/ssc8537/AutoClicker.git` |
| 程序目录 | `my-automation-tool/` |
| 源码入口 | `my-automation-tool/main.py` |
| 运行依赖 | `my-automation-tool/requirements.txt` |
| Python构建依赖 | `my-automation-tool/requirements-build.txt` |
| 原生录像构建 | `my-automation-tool/native-replay/BUILDING.md` |
| 支持系统 | Windows 10/11 64 位；主要验收环境为 Windows 11 |
| 推荐 Python | 64 位 CPython 3.12–3.14；当前发布环境为 Python 3.14.2 |
| 当前验证版本 | PySide6 6.11.1、pynput 1.8.2、keyboard 0.13.5 |

优秀案例目录不是运行依赖，GitHub 下载版没有它们也能完整启动。不要从网络补下案例源码来“修复依赖”。

## 2. 人类快速配置

### 第一步：下载项目

```powershell
git clone https://github.com/ssc8537/AutoClicker.git
cd AutoClicker
```

也可以在 GitHub 点击 `Code → Download ZIP`，解压后在该根目录打开 PowerShell。

### 第二步：创建独立 Python 环境

```powershell
py -3 -m venv .venv
```

若提示找不到 `py`，先确认 [python.org](https://www.python.org/downloads/windows/) 的 64 位 Python 已安装，再使用：

```powershell
python -m venv .venv
```

后续命令直接调用虚拟环境 Python，不要求激活环境，也不需要修改 PowerShell 执行策略。

### 第三步：安装依赖

```powershell
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r .\my-automation-tool\requirements.txt
```

### 第四步：先运行自动检查

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s .\my-automation-tool\tests -q
& .\.venv\Scripts\python.exe -m compileall -q .\my-automation-tool\main.py .\my-automation-tool\src .\my-automation-tool\tests
```

### 第五步：启动源码版

```powershell
& .\.venv\Scripts\python.exe .\my-automation-tool\main.py
```

每次启动后全局自动化默认为启用，但不会自动运行宏。先在“设置”确认“热键已启用”和当前全局启停键，再在“宏库/触发”检查目标脚本；不要假设固定为 F9 或 F12。第一次按全局键会禁用，再按一次恢复启用。

## 3. AI 执行协议

AI 接手后按顺序执行，不猜目录、不运行用户宏：

1. 确认当前目录同时存在 `AGENTS.md`、`README.md` 和 `my-automation-tool/main.py`；否则停止并定位仓库根目录。
2. 读取 `AGENTS.md`、`PRODUCT_REQUIREMENTS.md`、`PROJECT_ROADMAP.md`、`my-automation-tool/docs/handover/CURRENT_HANDOVER.md`。
3. 运行 `git status --short`，保护所有已有修改，尤其是 `macros/`、`config/`、`logs/`。
4. 检查 `py --version` 或 `python --version`；没有 Python 时只向用户说明安装步骤，不擅自下载安装软件。
5. 创建 `.venv`，使用 `.venv\Scripts\python.exe` 安装运行依赖。
6. 运行单元测试和 `compileall`。失败时先报告准确测试名；不得为了全绿擅自改动用户宏状态。
7. 只启动 `main.py` 检查 GUI；未经用户授权，不启用全局自动化、不执行真实宏、不进入游戏测试。
8. 成功标准：程序显示“自动连招”窗口；宏库、触发、功能、开发连招、设置五页存在；窗口可正常关闭；`logs/app.log`没有启动异常。没有编译原生核心时，录像页应明确提示“未找到录像核心”，不能冒充录像成功。

AI 可直接执行的 PowerShell：

```powershell
$ErrorActionPreference = 'Stop'
if (-not (Test-Path .\my-automation-tool\main.py)) { throw '当前不是 AutoClicker 仓库根目录' }
if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 -m venv .venv
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python -m venv .venv
} else {
    throw '未安装 Python 3，请先安装 64 位 CPython 3.12–3.14'
}
$python = (Resolve-Path .\.venv\Scripts\python.exe).Path
& $python -m pip install --upgrade pip
& $python -m pip install -r .\my-automation-tool\requirements.txt
& $python -m unittest discover -s .\my-automation-tool\tests -q
& $python -m compileall -q .\my-automation-tool\main.py .\my-automation-tool\src .\my-automation-tool\tests
```

## 4. 游戏与管理员权限

- 普通源码启动足以检查 UI、配置和记事本安全输入。
- 如果游戏以管理员身份运行，普通权限程序的 `SendInput` 可能被 Windows 权限隔离。
- 正式 EXE 已内置管理员清单；启动时出现 Windows UAC 提示属于预期。
- 不要关闭安全软件、安装驱动输入或绕过反作弊。管理员版仍无效时先检查 `logs/app.log`、游戏前台状态和 `SendInput` 返回。

## 5. 构建正式 EXE

先安装构建依赖：

```powershell
& .\.venv\Scripts\python.exe -m pip install -r .\my-automation-tool\requirements-build.txt
```

正式包还必须先具备`C:\MAPL-Native-Replay\`下的Rust/MSVC工具链。固定路径、构建命令和清理方法见：

```text
my-automation-tool\native-replay\BUILDING.md
```

在仓库根目录运行：

```powershell
$python = (Resolve-Path .\.venv\Scripts\python.exe).Path
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
    .\my-automation-tool\scripts\build_windows.ps1 -PythonExe $python
```

`-ExecutionPolicy Bypass` 只作用于这一次构建子进程，不会修改系统或当前用户的永久执行策略。

成功输出：

```text
my-automation-tool\dist\MyAutoPlayer\MyAutoPlayer.exe
```

构建为文件夹式便携版，包含管理员清单、统一图标、提示音、头像、原生录像核心、可交付`config/`和当前`macros/`。本机生成的`replay_settings.json`、`key_monitor.json`和`ai_prompt.complete.md`会从正式包排除，避免泄露绝对路径、设备选择和窗口位置。`build/`、`dist/`、`.spec`是本地生成物，不上传GitHub。

## 6. 可写数据与备份

- `my-automation-tool/macros/`：用户连招源码，只运行可信文件。
- `my-automation-tool/config/`：全局键、快捷连点、主题/布局、共享动作和 AI 提示词。
- `my-automation-tool/captures/`：原始视频、外挂字幕、按键日志和会话元数据；默认不上传GitHub。
- `my-automation-tool/logs/app.log`：排障日志；日志被 `.gitignore` 排除。
- 删除或覆盖 `macros/`、`config/` 前必须先得到用户明确授权。

## 7. 常见问题

### 找不到 `py` 或 `python`

安装 64 位 Python，并在安装器中勾选 `Add python.exe to PATH`；重新打开 PowerShell再验证 `python --version`。

### `pip install` 失败

确认网络正常，然后执行：

```powershell
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r .\my-automation-tool\requirements.txt
```

不要混用系统 Python 与 `.venv` Python。

### 程序能在记事本工作，游戏内无效

先运行管理员正式 EXE；确认游戏窗口在前台、脚本模式正确，并查看 `my-automation-tool/logs/app.log`。不要把发送权限问题误判为触发键失效。

### 中文输入法下字母表现异常

物理触发与输入法无关，但发送到目标窗口的字母会进入当前 IME。验收英文按键输出时切换英文输入法，并同时查看 OSD 与日志。

### 第二次启动提示程序已经运行

这是单实例保护。新版会唤醒并前置已经运行的窗口；仍找不到时检查任务栏和托盘，再从现有窗口正常退出，不要启动多个监听实例。

### 开发连招提示“未找到录像核心”

普通用户应使用完整文件夹式便携包，并确认下面两个文件同时存在：

```text
MyAutoPlayer.exe
native-replay\myautoplayer-native-replay.exe
```

源码开发者请按`my-automation-tool\native-replay\BUILDING.md`编译；`build_native_replay.ps1`是构建脚本，不是录像启动入口。
