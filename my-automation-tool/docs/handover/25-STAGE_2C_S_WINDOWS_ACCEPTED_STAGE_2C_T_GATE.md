# Stage 2C-S Windows 验收归档与 Stage 2C-T 门槛

日期：2026-07-18  
状态：历史实施前门槛快照；当前状态请看 `CURRENT_HANDOVER.md`  
Git：工作区已有未提交改动；本轮未提交、未推送

## 已确认事实

用户已按 `../test-plans/STAGE_2C_SWITCH_TIMING_MANUAL_TEST.md` 完成 Stage 2C-S 的 1–4 步 Windows 教程并确认全部通过。该阶段只验证提示词和作者规则文字，不运行真实游戏输入。

GoalAlignmentMonitor 首检为 **DRIFT**，原因是稳定入口仍称 Stage 2C-S “待验收”。`PROJECT_OUTLINE.md`、`REVIEW_LOG.md`、`CURRENT_HANDOVER.md`、产品决定和测试总表已更正；结论为 **ALIGNED**。历史 `24-STAGE_2C_SWITCH_TIMING_HANDOVER.md` 保持不改写。

## 唯一候选：Stage 2C-T

用户已授权审查：

- `config/ai_prompt.txt` 作为用户可编辑的 UTF-8 提示词；
- `config/ai_prompt.default.txt` 作为不可自动改写的人工恢复备份；
- 提示词窗口重开时重新读取、显示绝对路径和读取失败的安全回退；
- `player.tap("R")` 后立即 `player.sleep(1800)` 的作者时序文字规则。

本快照记录的是实施前门槛：当时尚未实施，必须先由本次接手唯一一次 RequirementCertifier 产出 READY。之后的实际实施、自动检查与 Windows 验收状态以 `CURRENT_HANDOVER.md` 和后续编号交接为准。Stage 2D、鼠标、角色/技能语义 API、键位配置、F9/F12/F2、真实输入与宏执行不在范围内。

## 恢复入口

先读取本文件、`CURRENT_HANDOVER.md`、`CURRENT_PRODUCT_DECISIONS.md`、`REVIEW_LOG.md` 和 `REQUIREMENT_READINESS_GATE.md`，再对 Stage 2C-T 作独立 READY/NOT READY 审查。
