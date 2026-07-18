# Stage 4T 实施完成，等待 Windows 验收

日期：2026-07-18
状态：自动验证完成；未启动真实 GUI；等待 Windows 任务栏/托盘验收

## 已实现

- 自有 Candy 粉红标题栏三动作：`×` 直接退出、`—` 最小化到任务栏、`藏` 隐藏到托盘。
- 标题栏可拖动；底部细条只能改变窗口高度，642 宽度保持不变。
- 使用 Qt 标准图标的托盘菜单：“显示主窗口”“隐藏主窗口”“退出程序”；单击托盘图标恢复窗口。
- `×` 与托盘退出共用既有 `closeEvent`，因此停止活动宏、释放输入、取消热键并退出；隐藏/最小化不改变 F12 或宏状态。
- 无系统托盘时，隐藏按钮禁用，程序仍可最小化与安全退出。

## 自动证据

在 `my-automation-tool` 目录执行：

- `python -m unittest discover -s tests -v`：62/62 通过。
- `python -m compileall -q main.py src tests`：通过。
- `git diff --check`：通过。

离屏测试覆盖三按钮、托盘菜单、可用/不可用回退、隐藏/恢复、最小化、退出和纵向缩放；未启动真实 GUI 或发送输入。

## 当前唯一用户动作

按 `../test-plans/STAGE_4T_TRAY_WINDOW_MANUAL_TEST.md` 在 Windows 验收。通过前不进入多宏、独立代码清理或发布；默认不提交、不推送。
