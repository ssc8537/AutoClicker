# MyAutoPlayer（自动连招）

面向 Windows 11 的个人游戏键鼠自动化工具。程序使用 Python + PySide6；每个连招是一个可阅读、可编辑、可停止的本地 Python `run(player)` 宏，不使用案例 JSON/QIM 作为运行格式。

> 只运行你信任的宏文件。正式 EXE 会请求管理员权限，以便与可能以管理员身份运行的游戏保持同一权限层级。

## 当前完整功能

- 宏库：新建、编辑、静态校验、保存、改名、删除和 AI 提示词。
- 独立触发：每个宏可设置一个键盘键或五鼠标键，支持“按下/切换”、次数、速度、即时启用；同键可并发多个宏。
- 全局安全：全局启停键可自定义；停止、禁用和退出都会释放输入并清理监听。
- 功能页：一排快捷连点，以及名称/物理键均可编辑的共享游戏动作。
- 桌面体验：OSD、提示音、托盘、统一角色图标、无黑窗管理员 EXE、单实例运行。
- 双外观：经典粉红/樱空花园主题与顶部标签/画册侧栏布局可独立组合，一键恢复经典。
- 画册侧栏：用户动漫头像、居中导航；窗口支持上下左右及四角缩放。
- AI 脚本作者：提示词会动态加入当前全局键、共享动作、支持按键和完整脚本 API。

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

输出：`my-automation-tool\dist\MyAutoPlayer\MyAutoPlayer.exe`。`dist/` 是本机构建产物，不提交到 GitHub。

## 重要目录

| 路径 | 用途 |
|---|---|
| `my-automation-tool/main.py` | 程序入口 |
| `my-automation-tool/src/` | 核心逻辑与 UI |
| `my-automation-tool/macros/` | 用户 Python 连招 |
| `my-automation-tool/config/` | 全局键、主题、共享动作、提示词等配置 |
| `my-automation-tool/assets/` | 图标、提示音和画册头像 |
| `my-automation-tool/tests/` | 自动回归测试 |
| `PRODUCT_REQUIREMENTS.md` | 当前全部真实产品需求 |
| `PROJECT_ROADMAP.md` | 唯一阶段路线与进度 |

## AI 接手入口

AI 依次读取：`AGENTS.md` → `PRODUCT_REQUIREMENTS.md` → `PROJECT_ROADMAP.md` → `my-automation-tool/docs/handover/CURRENT_HANDOVER.md` → `SETUP_GUIDE.md`，然后运行 `git status --short`。不得执行、覆盖或清理用户 `macros/`、`config/`、`logs/`；默认不提交、不推送，只有用户明确要求才发布。

优秀案例源码仅在本地用于只读行为核对，已被 `.gitignore` 排除，不是运行依赖，也不会上传 GitHub。
