# Stage 2D 触发表格视觉修订实施交接

日期：2026-07-18  
状态：自动检查完成；Windows 人工验收待进行  
Git：工作区已有未提交改动；本轮未提交、未推送

## 已完成

- 用户已确认 Stage 2C-U 教程 1–4 通过；历史教程和编号交接未改写。
- 触发页表格已从四列改为“序号、名称、按键、模式、状态”五列；序号由当前行从 1 连续生成。
- 名称只显示 `Path.stem`，因此不显示 `.py`；磁盘文件名、宏解析、选择路径与运行路径未改变。
- 所有表头和单元格居中。状态列已从旧第 4 列迁移到新第 5 列，仍是唯一启用/停用入口；无效名称继续红字，右侧详情继续只读。
- 新增 `../test-plans/STAGE_2D_TRIGGER_TABLE_VISUAL_MANUAL_TEST.md`；不改 F9/F12/F2、OSD、fail-closed、宏执行或真实输入。

## 自动检查

在 `my-automation-tool` 执行：

- `python -m unittest discover -s tests -v`：41/41 通过。
- `python -m compileall -q main.py src macros`：通过。
- `git diff --check`：通过；仅有既有工作区文件的 CRLF 警告。

离屏测试覆盖五列表头、连续序号、去 `.py`、居中、无效红字、状态列唯一启停、右侧详情与横向滚动/F9/F12/F2 回归。未启动真实 GUI，未发送真实输入。

AntiHallucination：PASS（附拆分报告）。`main.py` 为 545 行，已超过阈值；`../reviews/STAGE_2D_MAIN_LENGTH_SPLIT_REPORT.md` 说明其长期拆分方向。Stage 2D 未获重构 READY，因此本轮不拆分、保留稳定入口；`tests/test_ui_shell.py` 为 498 行且职责单一。

## 仍需用户操作

按 `../test-plans/STAGE_2D_TRIGGER_TABLE_VISUAL_MANUAL_TEST.md` 做 Windows 验收。通过前只修复该教程可复现问题；不得进入 Stage 3K、Stage 3M、Stage 4T、鼠标、键位配置、角色/技能语义 API、多宏或新热键。

## 恢复入口

先读 `CURRENT_HANDOVER.md`、本文件、`REVIEW_LOG.md`、`CURRENT_PRODUCT_DECISIONS.md` 和 Stage 2D 教程。用户确认后只归档本阶段验收结果；默认不提交、不推送。
