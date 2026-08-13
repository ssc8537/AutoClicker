# MyAutoPlayer（自动连招）

面向 Windows 11 的个人游戏键鼠自动化工具。程序使用 Python + PySide6；每个连招是一个可阅读、可编辑、可停止的本地 Python `run(player)` 宏，不使用案例 JSON/QIM 作为运行格式。

当前版本：Stage 20 鼠标 X/Y 相对移动、固定压枪宏与麦克风预检已完成并通过验收。默认主干`master`保存当前发布源码，历史标签与Git提交仍可用于回退旧版本。

> 只运行你信任的宏文件。正式 EXE 会请求管理员权限，以便与可能以管理员身份运行的游戏保持同一权限层级。

## 当前完整功能

- 宏库：新建、编辑、静态校验、保存、改名、删除和 AI 提示词。
- 独立触发：每个宏可设置一个键盘键或五鼠标键，支持“按下/切换”、次数、速度、即时启用；同键可并发多个宏。
- 全局安全：每次启动默认启用但不会自动运行宏；全局启停键可自定义，停止、禁用和退出都会释放输入并清理监听。
- 功能页：一排快捷连点，以及名称/物理键均可编辑的共享游戏动作。
- 鼠标相对移动：Python 宏可立即或平滑发送 X/Y 相对位移；停止、禁用和退出都会中断尚未发送的平滑步骤。
- 桌面体验：OSD、循环次数提示、提示音、托盘、统一角色图标、无黑窗管理员 EXE、单实例唤醒并前置。
- 当前唯一外观：樱空花园主题与画册侧栏；用户动漫头像、居中导航，窗口支持上下左右及四角缩放。
- AI 脚本作者：提示词动态加入当前全局键、共享动作、完整按键字典、宏源码和录像事件字段说明。
- 开发连招：项目内原生全屏回放缓冲，720p/1080p与15/30/45/60fps可选，GPU/CPU编码显式选择；不调用OBS。
- 声音与复盘：桌面声音和可选麦克风保存为独立音轨；桌面音量可在0–300%调整。麦克风预检每次启动默认关闭，用户主动开启后才打开所选麦克风并显示真实电平。保存会话包含`raw.mp4`、按键JSONL/CSV、ASS/SRT外挂字幕和元数据。
- 按键记录窗口：全局物理按键down/up毫秒时间线、按键高亮、最近3/5/10条事件、透明度/缩放/位置记忆；最小化后可从“开发连招”重新唤回。
- 历史录像：按日期浏览，播放原始视频、打开字幕或目录；明确选择并二次确认后才移入Windows回收站。

> 原生回放只记录用户选择的完整显示器、允许的物理键和声音，不读取游戏内存、不注入游戏、不记录鼠标移动，也不生成烧录字幕的`perfect.mp4`。

## 鼠标移动宏

`player.mouse_move(x, y, duration_ms=0)` 只相对当前位置移动，不读取光标位置，也不是绝对屏幕坐标：X 正数向右、X 负数向左；Y 正数向下、Y 负数向上。`duration_ms=0` 立即移动，大于 0 时在指定真实毫秒内平滑移动，且不受 `SPEED` 缩放。

```python
NAME = "鼠标相对移动练习"      # 宏库显示名称
HOTKEY = "f6"                 # 物理触发键：F6
MODE = "down"                 # 按住运行，松开立即停止
COUNT = 1                      # 只运行一轮
SPEED = 1.0                    # 只影响 player.sleep
ENABLED = True                 # 在宏库中启用

def run(player):
    # 在120ms内向右120、向上30；松开触发键会中断后续移动。
    player.mouse_move(120, -30, duration_ms=120)
    player.sleep(200)
    # 立即向左移动120、向下移动30。
    player.mouse_move(-120, 30)
```

Windows“鼠标指针速度”“增强指针精确度”、游戏内灵敏度和目标游戏是否接受 `SendInput`，都会影响肉眼看到的移动距离。请先在空白桌面、画图或游戏安全训练区域验收。程序仍不支持绝对坐标、读取当前位置、真实轨迹录制/回放和滚轮自动化；开发连招录像也仍然不会记录鼠标移动。

项目已提供可直接验收的 `my-automation-tool/macros/z-自动压枪宏.py`：按住反斜杠键时按住鼠标左键，并每15ms相对向下移动1个单位；松开后立即停止并释放左键。本版本使用固定值，不包含随机化。

## 版本更新：Stage 20

- 新增 `player.mouse_move(x, y, duration_ms=0)` 相对 X/Y 移动 API。
- 支持立即移动与约 10ms 一步的平滑移动，整数累计无取整漂移。
- `down` 松开、`switch` 再按、全局禁用与程序退出可及时停止后续平滑步骤。
- 所有移动继续使用 Windows `SendInput` 和 `MAPL` 安全标记；AI 提示词、产品需求和教程已同步。
- 未加入绝对坐标、当前位置读取、轨迹录制/回放、滚轮、识别或驱动输入。
- 开发连招页新增独立“麦克风预检”开关：每次启动默认关闭，关闭时原生核心不打开麦克风；需要测试时再手动开启。

## 下载后快速启动

完整的人类/AI 共用配置说明见：[SETUP_GUIDE.md](SETUP_GUIDE.md)。最短 PowerShell 流程：

```powershell
git clone https://github.com/ssc8537/AutoClicker.git
cd AutoClicker
py -3 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r .\my-automation-tool\requirements.txt
& .\.venv\Scripts\python.exe .\my-automation-tool\main.py
```

如果电脑没有 `py` 命令，把第一条 Python 命令改为 `python -m venv .venv`。

## 自动检查

```powershell
cd AutoClicker
& .\.venv\Scripts\python.exe -m unittest discover -s .\my-automation-tool\tests -q
& .\.venv\Scripts\python.exe -m compileall -q .\my-automation-tool\main.py .\my-automation-tool\src .\my-automation-tool\tests
git diff --check
```

自动测试不会主动运行用户真实连招。真实键鼠输入请先在记事本或游戏安全训练区域人工验收。

## 构建 Windows 便携版

```powershell
& .\.venv\Scripts\python.exe -m pip install -r .\my-automation-tool\requirements-build.txt
$python = (Resolve-Path .\.venv\Scripts\python.exe).Path
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
    .\my-automation-tool\scripts\build_windows.ps1 -PythonExe $python
```

正式构建还需要固定位置的Rust/MSVC工具链，详见[原生录像构建说明](my-automation-tool/native-replay/BUILDING.md)。输出为`my-automation-tool\dist\MyAutoPlayer\MyAutoPlayer.exe`，原生核心位于同包的`native-replay\`。`dist/`是本机构建产物，不提交到GitHub。

普通用户不要双击`build_native_replay.ps1`；下载正式便携包后只运行`MyAutoPlayer.exe`。源码启动可以查看和使用宏功能，但必须先编译原生核心才能使用录像。

## 重要目录

| 路径 | 用途 |
|---|---|
| `my-automation-tool/main.py` | 程序入口 |
| `my-automation-tool/src/` | 核心逻辑与 UI |
| `my-automation-tool/native-replay/` | Rust原生全屏/双音轨回放源码与第三方许可 |
| `my-automation-tool/macros/` | 用户 Python 连招 |
| `my-automation-tool/config/` | 全局键、主题、共享动作、提示词等配置 |
| `my-automation-tool/captures/` | 本机录像会话；默认被Git忽略 |
| `my-automation-tool/assets/` | 图标、提示音和画册头像 |
| `my-automation-tool/tests/` | 自动回归测试 |
| `PRODUCT_REQUIREMENTS.md` | 当前全部真实产品需求 |
| `PROJECT_ROADMAP.md` | 唯一阶段路线与进度 |
| `SETUP_GUIDE.md` | 人类与 AI 共用的安装、运行和构建入口 |
| `my-automation-tool/docs/handover/CURRENT_HANDOVER.md` | 当前版本状态、边界与接手说明 |
| `my-automation-tool/native-replay/BUILDING.md` | 原生录像核心的可复现构建与工具清理说明 |

## AI 接手入口

AI 依次读取：`AGENTS.md` → `PRODUCT_REQUIREMENTS.md` → `PROJECT_ROADMAP.md` → `my-automation-tool/docs/handover/CURRENT_HANDOVER.md` → `SETUP_GUIDE.md`，然后运行 `git status --short`。不得执行、覆盖或清理用户 `macros/`、`config/`、`logs/`；默认不提交、不推送，只有用户明确要求才发布。

优秀案例源码仅在本地用于只读行为核对，已被 `.gitignore` 排除，不是运行依赖，也不会上传 GitHub。

本机生成的`replay_settings.json`、`key_monitor.json`和`ai_prompt.complete.md`同样不会上传或进入正式便携包，避免发布个人保存路径、设备选择和窗口位置。
