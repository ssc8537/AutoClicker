# 当前测试总表

## Stage 4T：Windows 验收通过；粉色图标目测待做

- 用户已确认原教程 1–5：最小化、隐藏、托盘菜单/恢复、纵向缩放、安全退出和 F9/F12/F2 回归均通过。
- 本轮自动检查：全量单元测试、编译与差异检查通过；离屏测试确认窗口图标非空、托盘复用同一图标。
- 仅剩人工：重启程序后在 Windows 任务栏与通知区域确认粉色图标；见 `my-automation-tool/docs/test-plans/STAGE_4T_TRAY_WINDOW_MANUAL_TEST.md`。

## 永久测试原则

每个新小阶段先有自动测试，涉及 UI/真实输入再给普通 Windows 用户的中文教程。AI 不把离屏检查写成真实输入或 Windows 视觉验收。
