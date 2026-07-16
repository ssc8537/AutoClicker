# 5-给下一位AI工作-V022视觉确认与V023审查

> 日期：2026-07-16

## 当前基线

- 当前分支：`codex/v021-ui-shell`。
- 已发布基线：`1c3b141`（v022 路线图纠偏与目标监控归档），GitHub `master` 与功能分支均指向该提交；接手时必须重新核验远端。
- 用户已确认：V022 Candy 粉红四页视觉规格通过。
- 当前代码边界不变：可信本地 Python 宏；F9 执行、F12 唯一全局开关、F2 仅占位；案例只读且不提交。

## 必须调用顺序

1. 读取 `AGENTS.md`、`.codex/agents/1-project-lead.md`、`1-团队员工说明.md`、`CURRENT_HANDOVER.md` 和本文件。
2. 第一员工：GoalAlignmentMonitor，重新核验 `ALIGNED/DRIFT/UNKNOWN`。
3. 第二员工：RequirementCertifier，审查 V023 的实施 READY/NOT READY。

## V023 唯一候选范围

只允许在 RequirementCertifier READY 后，调整 `my-automation-tool/main.py` 的 `MainWindow._setup_ui()` 和四个 `_build_*_page()` 中的布局、文案、间距及 Candy 样式，以落实 `docs/requirements/V022_VISUAL_ALIGNMENT_SPEC.md`。

禁止：修改窗口固定宽 642、最小高 510、F9/F12/F2 注册、OSD、播放器、关闭清理、真实输入；禁止实现宏库管理、脚本编辑、鼠标、窗口、音效、多脚本、录制、定时或案例资源。

## 实施后必须验收

1. 离屏 UI 测试与现有 F9/F12/F2/关闭清理回归。
2. AntiHallucination、RealtimeChecker、TestEngineer、ProjectManager、DocUpdater 与 Handover 复核。
3. 用户在 Windows 对照四页外观，并在记事本回归 F12、F9、F2。

## 当前未完成项

- GoalAlignmentMonitor 最终为 **ALIGNED**；RequirementCertifier 对 V023 最终为 **READY**。本线程仍未写任何 V023 UI 代码，实施交给下一位 AI。
- 本轮用户确认和本交接为未提交文档草稿；提交前必须再次调用 AntiHallucination，暂存范围只含本轮文档，再按 GitHub SOP 先推功能分支、后快进 `master` 并核验 SHA。
