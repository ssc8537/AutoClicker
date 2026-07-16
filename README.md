# MyAutoPlayer

一个面向个人使用的 Windows 键盘自动化工具。它借鉴 Quickinput 的宏库、热键和界面组织方式，使用 Python/PySide6 实现；用户宏使用可信本地 Python 文件，不使用 JSON 作为运行格式。

## 当前可用功能

- F12：全局启用/禁用所有脚本；禁用时立即停止当前宏并显示 OSD。
- F9：运行 `my-automation-tool/scripts/hello_world.py`。
- 两种模式：`switch` 与 `down`；`COUNT = 0` 时按住 F9 循环、松开停止。
- 每次 F9 前重新读取已保存的 Python 宏；`tap()` 和 `sleep()` 可被停止请求中断。

## 安装与启动

在 Windows PowerShell 中执行：

```powershell
cd C:\Users\s\Desktop\1-test\1-自动连点器\my-automation-tool
python -m pip install -r requirements.txt
python main.py
```

详细环境说明见 `SETUP_GUIDE.md`。程序启动后，先按 F12 看到绿色“全局脚本已就绪”，再把鼠标移出程序窗口并在记事本测试 F9。

## 测试

```powershell
cd C:\Users\s\Desktop\1-test\1-自动连点器\my-automation-tool
python -m unittest discover -s tests -v
python -m compileall -q main.py src scripts
```

人工测试步骤见 `my-automation-tool/docs/USER_TEST_GUIDE.md`。自动测试不会发送真实键盘输入；真实输入仅由你手动启动程序后触发。

## 贡献与团队协作

- 运行代码前先阅读 `PROJECT_STRUCTURE.md`、`my-automation-tool/PROJECT_SPEC.md` 与 `docs/handover/CURRENT_HANDOVER.md`。
- 团队角色配置位于 `.codex/agents/`；小白使用方法见 `my-automation-tool/docs/team/TEAM_USAGE_GUIDE.md`。
- 两份优秀案例只在本地只读参考，禁止提交或复制源码。
- 每次功能里程碑必须更新文档、测试记录、交接文档，并先创建可回退 Git 基线。
