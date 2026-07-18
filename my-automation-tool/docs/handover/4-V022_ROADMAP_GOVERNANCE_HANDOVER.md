# 4-给下一位AI工作-V022路线图纠偏与治理归档

> 日期：2026-07-16

## 当前稳定事实

- 分支：`codex/v021-ui-shell`；已发布基线：`bc06485`。GitHub 默认分支 `master` 与功能分支均已指向该提交。
- v021 的运行/安全验收通过；Candy 粉红方向得到用户认可，但视觉最终取舍尚未确认。
- V022 只产出视觉规格和人类确认清单，禁止修改 UI、F9/F12/F2、OSD、播放器、窗口规则或真实输入。

## 已有验证证据

- v021 基线：23/23 单元测试、Python 编译、离屏 UI 截图与 `git diff --check` 通过；用户已完成 F9/F12/F2 运行与安全验收。
- 本轮只改 Markdown 与角色配置，不运行自动测试或真实输入。TestEngineer 已确认 V022 清单是视觉规格确认，不需要重测 F9/F12/F2；当时的文件与规格复核均通过。

## 最高调用顺序（必须执行）

1. 读取 `AGENTS.md`、`.codex/agents/1-project-lead.md` 和 `1-团队员工说明.md`。
2. **第一员工：GoalAlignmentMonitor**，输出 `ALIGNED/DRIFT/UNKNOWN`。
3. **第二员工：RequirementCertifier**，输出 `READY/NOT READY`。
4. 有偏离或证据缺口时，先用 CodeExplorer、KnowledgeExpert、UIReferenceAnalyst 补证，再由 DocUpdater/Handover 归档；未经两道门不得实现。

## 本轮已完成

- 新增 `0-goal-alignment-monitor.md`，把总目标、路线、验收、边界和归档连续性设为最高审查门。
- 新增根目录 `1-团队员工说明.md`，供人类按编号查看所有员工、职责和调用顺序。
- 新增 V022 视觉规格与用户确认清单；新增路线图—优秀案例对齐审查。
- 纠正阶段测试总览：Python 运行时为已验收主线；JSON 为历史基线；窗口、音效、鼠标、多脚本、任意热键等为候选而非承诺。
- GitHub 成功普通快进 SOP 已归档到 `LESSONS_LEARNED.md`。

## 未完成与风险

- GoalAlignmentMonitor 首次结论为 **DRIFT**，原因是旧交接调用顺序和归档缺失；调用顺序、路线图和归档已纠正，第三次复审为 **ALIGNED**。本轮仍需 AntiHallucination 终检与 RequirementCertifier 文档提交复审。
- RequirementCertifier 最终为 **READY（仅本轮文档与角色配置提交）**；UI、宏库和候选扩展代码仍 **NOT READY**。
- “最终完整项目”范围为 **UNKNOWN**：用户尚未锁定多 Python 宏、每宏热键、编辑/持久化和高级扩展是否属于最终产品。
- S1.5 的用户通过陈述与旧清单未勾项需后续对齐；不得把未执行测试补写为通过。

## 用户当前需要做什么

阅读 `my-automation-tool/docs/test-plans/V022_VISUAL_SPEC_CONFIRMATION.md` 并逐项确认视觉取舍。此阶段不是运行测试，不要重复运行 F9/F12/F2；后续 UI 实现获 READY 后才提供新的 Windows 验收教程。

## 唯一下一步

完成本轮仅文档/角色配置的暂存审查、提交和 GitHub 发布核验；发布完成后把上述 V022 视觉规格确认清单交给用户。本文形成时本轮草稿尚未提交，下一位 AI 必须重新核对 Git 状态，不能假定远端已更新。

## 提交前后固定动作

1. AntiHallucination 复查事实、行数、职责和编码。
2. TestEngineer、DocUpdater 核对测试说明、运行边界、引用和归档。
3. `git diff --check`、暂存范围检查后仅提交本轮文档/角色配置。
4. 若用户明确要求发布，按已验证 GitHub SOP 普通推送功能分支和 `master`，并以 `ls-remote --symref` 核验 SHA。
