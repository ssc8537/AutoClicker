# 10-给下一位AI工作-C1自动检测与唯一活动状态实现交接

> 日期：2026-07-17｜状态：实现与自动验证完成；等待 Windows/记事本人工验收。

## 已完成

- 用户批准计划后，GoalAlignmentMonitor 纠正文档 `DRIFT` 并复审 **ALIGNED**；RequirementCertifier 对自动检测扩展及后续职责拆分均给出受限 **READY**。
- 宏库不再提供“刷新”或“设为活动宏”。`QFileSystemWatcher` 在 Qt 主线程监听目录和文件，以 150ms 单次防抖自动更新；监听与扫描使用 AST 静态校验，绝不执行宏顶层代码。
- 表格分开显示“文件校验”和“活动状态”。有效宏可点击启用/再次点击停用，始终只有一个活动宏；无效项显示中文错误且不可启用。活动文件删除或失效时会停播、`mark_finished("f9")`、清空选择并让 F9 fail-closed。
- F9 才通过运行时 `reload()` 加载活动宏；F12 仍为唯一总开关，F2 仍仅占位。触发页会随活动宏同步显示脚本、模式、次数和速度。
- 新增 `macros/invalid_missing_run.py`；保留 `hello_world.py` 与 `goodbye.py`。
- 为控制文件职责，`main.py` 已拆为 409 行，宏库页面/监听位于 `src/ui/macro_library_panel.py`（165 行）；报告见 `docs/reviews/C1_MAIN_SPLIT_REPORT.md`。

## 验证与人工验收

- `python -m unittest discover -s tests -v`：29/29 通过。
- `python -m compileall -q main.py src macros`、`git diff --check`：通过。
- 尚未启动真实 GUI 或发送真实输入。用户须按 `docs/test-plans/C1_MANUAL_TEST.md` 在记事本验证无活动 F9、hello/goodbye 切换、保存后自动更新、无效项、活动宏删除/改坏和 F12。

## Git 与边界

- 保留当前未提交工作区；不清理、不提交、不推送。远端状态仍需发布前实时核验。
- 禁止编辑、保存、重命名、创建、多宏并发、每宏热键、鼠标、窗口、音效、录制、定时、JSON/QIM；不得改 F9/F12/F2/OSD 安全边界。
- 用户人工验收通过前，下一位 AI 只可诊断和归档反馈，不得发布。
