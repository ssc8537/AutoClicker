# Stage 2C-T Windows 验收归档与 Stage 2C-U READY

日期：2026-07-18  
状态：Stage 2C-T 已验收；Stage 2C-U 已 READY、实施中  
Git：工作区已有未提交改动；本轮未提交、未推送

## 已确认事实

用户已按 `../test-plans/STAGE_2C_EDITABLE_PROMPT_MANUAL_TEST.md` 完成 Stage 2C-T 的 1–6 步并确认全部通过。该验收不运行游戏输入。历史教程与 `26-STAGE_2C_T_EDITABLE_PROMPT_IMPLEMENTATION_HANDOVER.md` 保持不改写。

GoalAlignmentMonitor 首检为 **DRIFT**，原因是稳定入口仍写 Stage 2C-T 待 Windows 验收；`PROJECT_OUTLINE.md`、`STAGE_TEST_PLAN.md`、`REVIEW_LOG.md`、当前交接和产品决定已归档纠正，结论为 **ALIGNED**。

## Stage 2C-U 范围与门槛

RequirementCertifier 实施前终审为 **READY（仅受限范围）**。只允许同步两份提示词模板、作者手册、自动测试、新中文 Windows 教程和稳定文档：

- 六个不同角色方向的普通切人前至少等待 50ms；
- A→B 后立即 B→A 的回切为 1080ms（1000ms 冷却 + 80ms 安全余量）；
- `player.tap("R")` 后紧邻 `player.sleep(1500)`；该等待覆盖后续普通和回切门槛，结束后可直接发其他 `1`/`2`/`3`。

不得改热键、真实输入、宏执行、UI、动画/CD/当前角色检测、角色语义 API 或任何后续阶段能力。模板文字不代表新增运行时能力。

## 完成条件与恢复入口

自动断言双模板一致、六方向与三项数值、R 示例不插入 50ms/1080ms；保留提示词恢复、UTF-8 失败不覆盖、宏源码只读附带和 F9/F12 回归。通过后创建独立中文教程并等待用户 Windows 验收；默认不提交、不推送。

下一位 AI 先读 `CURRENT_HANDOVER.md`、本文件、`REVIEW_LOG.md`、`CURRENT_PRODUCT_DECISIONS.md` 和新 Stage 2C-U 教程；仅修复本教程可复现问题。
