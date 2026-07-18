# Stage 2C-U Windows 验收归档与 Stage 2D READY

日期：2026-07-18  
状态：Stage 2C-U 已验收；Stage 2D 已 READY、实施中  
Git：工作区已有未提交改动；本轮未提交、未推送

## 已确认事实

用户已按 `../test-plans/STAGE_2C_U_SWITCH_TIMING_REVISION_MANUAL_TEST.md` 完成 Stage 2C-U 的 1–4 步并确认全部通过。该验收不运行游戏输入；历史教程和编号交接保持不改写。

GoalAlignmentMonitor 首检为 **DRIFT**，原因是稳定入口仍写 Stage 2C-U 待验收。`PROJECT_OUTLINE.md`、`STAGE_TEST_PLAN.md`、`REVIEW_LOG.md`、当前交接和产品决定已归档纠正，结论为 **ALIGNED**。

## Stage 2D 范围与门槛

RequirementCertifier 实施前终审为 **READY（仅受限范围）**。只允许：

- 触发页表格新增从 1 连续编号的“序号”列；
- 宏名显示去 `.py` 的主体；
- 所有表头和单元格居中；
- 同步离屏测试、新中文 Windows 教程和稳定文档。

不得改变文件名、宏解析、选择路径、唯一启用/停用、无效红字、右侧只读详情、F9/F12/F2、OSD、fail-closed、宏执行或真实输入。根目录 `2-UI图片/2-触发.png` 与优秀案例 1 `TriggerUi.cpp` 仅作列层级视觉证据，绝不复制其源码、资源或品牌。

## 完成条件与恢复入口

自动断言五列表头、连续序号、无 `.py` 显示、全列居中、状态列唯一启停、无效红字、右侧详情与横向滚动/F9/F12/F2 回归。通过后生成独立中文教程，等待用户 Windows 验收；默认不提交、不推送。
