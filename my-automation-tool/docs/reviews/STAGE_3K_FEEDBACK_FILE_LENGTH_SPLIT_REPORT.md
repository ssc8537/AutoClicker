# Stage 3K 反馈修复文件长度拆分报告

日期：2026-07-18  
审查者：AntiHallucination + 项目负责人  
结论：本轮不扩大拆分；保持稳定入口和单一离屏回归入口

## 当前长度

- `main.py`：581 行。它是稳定应用入口，仍同时承担主窗口装配、页面构建、触发投影和热键协调。
- `tests/test_ui_shell.py`：581 行。它仍是单一的离屏主窗口回归集合。
- `src/core/macro_file_manager.py`：236 行；`src/core/game_keybinds.py`：123 行；`src/ui/macro_library_panel.py`：417 行；`src/ui/game_keybinds_panel.py`：73 行，均未超阈值且职责单一。

## 已获准的拆分与本轮边界

Stage 3K 的 READY 已授权把键位配置 UI 提取到 `src/ui/`，该项已完成。反馈修复只在 `main.py` 增加设置页滚动、删除协调和活动路径同步；宏库交互集中于既有 `macro_library_panel.py`，文件事务集中于 `macro_file_manager.py`。

继续拆分主窗口其余职责，或将离屏回归测试拆成多个测试模块，会改变稳定入口和测试组织，超出本轮“设置页可见、删除、启用宏编辑”READY 范围。未来独立代码清理阶段必须重新锁定模块边界、迁移断言和回退方案后才可进行。
