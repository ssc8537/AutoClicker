# MyAutoPlayer

一个面向个人使用的 Windows 键盘自动化工具。它借鉴 Quickinput 的宏库、热键和界面组织方式，使用 Python/PySide6 实现；用户宏使用可信本地 Python 文件，不使用 JSON 作为运行格式。

## 当前可用功能

- 宏库可新建、编辑、校验、改名和删除可信本地 Python `run(player)` 宏。
- 每个宏可自定义一个键盘键或五鼠标键，支持 `switch` 与 `down`、次数、速度和即时启用；同键可并发多个宏。
- 全局启停键可自定义；F2、F9、F12 均没有固定功能。禁用或退出时会停止脚本并释放输入。
- 功能页提供一排快捷连点，以及名称和物理键都可修改的共享游戏动作。
- 设置页可控制 OSD 与提示音；窗口、任务栏、托盘和无黑窗 EXE 使用用户角色图标。
- “AI 提示词”会动态加入当前共享动作、全局键、全部支持按键和完整脚本 API，供外部 AI 编写连招。

## 安装与启动

在 Windows PowerShell 中执行：

```powershell
cd C:\Users\s\Desktop\1-test\1-自动连点器\my-automation-tool
python -m pip install -r requirements.txt
python main.py
```

详细环境说明见 `SETUP_GUIDE.md`。程序启动后，先查看设置页的当前全局启停键，再在宏库启用脚本并在触发页设置它自己的触发键。真实输入只在记事本或安全区域测试。

## 测试

```powershell
cd C:\Users\s\Desktop\1-test\1-自动连点器\my-automation-tool
python -m unittest discover -s tests -v
python -m compileall -q main.py src scripts
```

人工测试步骤见 `my-automation-tool/docs/USER_TEST_GUIDE.md`。自动测试不会发送真实键盘输入；真实输入仅由你手动启动程序后触发。

## AI 接手与阶段开发

- 新 AI 默认只读 `AGENTS.md`、`PROJECT_ROADMAP.md`、`my-automation-tool/docs/handover/CURRENT_HANDOVER.md`，并运行 `git status --short`。
- `PROJECT_ROADMAP.md` 是唯一阶段计划；每轮完成实现或用户验收后都必须原地更新，禁止新建第二份根路线。
- 只在开始当前阶段时读取对应的一页需求与验收教程；历史阶段文档只作证据，不是接手入口。
- 优秀案例仅在需要时只读核对，禁止复制源码、资源、品牌或格式。
- 用户明确要求发布时才创建 Git 回退版本；默认不提交、不推送。
