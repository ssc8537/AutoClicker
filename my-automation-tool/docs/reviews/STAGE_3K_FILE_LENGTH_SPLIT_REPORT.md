# Stage 3K 文件长度拆分报告

日期：2026-07-18  
审查者：AntiHallucination + 项目负责人  
结论：本轮不再扩大重构；已完成获准的键位 UI 提取

## 事实

- `main.py` 为 550 行。此前 Stage 2D 已报告其超过 500 行；Stage 3K 的 READY 明确授权提取键位配置 UI，因此本轮已将可编辑映射区置于 `src/ui/game_keybinds_panel.py`，`main.py` 仅保留导入、创建和装配。
- `tests/test_ui_shell.py` 现超过 500 行。它仍是单一的离屏主窗口回归入口；新增内容只验证设置页的键位面板和已发布提示词。
- 新建 `src/core/game_keybinds.py`（123 行）与 `src/ui/game_keybinds_panel.py`（69 行）均不足 500 行且职责单一。

## 评估与边界

继续拆分 `main.py` 的其余主窗口/触发表职责，或把既有离屏测试拆到多个模块，会改变更大的调用与测试组织面。用户批准的 Stage 3K 重构范围仅是键位配置 UI 提取，已完成；没有获得独立代码清理 READY，因此本轮不做额外拆分。

## 后续门槛

未来独立代码清理阶段必须先取得 RequirementCertifier READY，锁定 `main.py` 稳定入口、测试模块边界、迁移断言和回退方案。Stage 3M 鼠标与 Stage 4T 托盘不能把这一报告当作实现许可。
