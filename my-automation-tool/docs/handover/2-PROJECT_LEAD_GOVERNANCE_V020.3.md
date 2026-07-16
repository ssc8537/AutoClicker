# 2-项目负责人提示词与团队流程审查

日期：2026-07-16

建议任务标题：`2-项目负责人提示词与团队流程审查`

分支：`codex/v020-team-ui-spec`

## 交接结论

v020.3 团队治理任务已经 RequirementCertifier 终审为 **READY** 并完成。新增 `.codex/agents/1-project-lead.md` 作为唯一总入口，项目负责人负责范围、员工调度、证据整合、测试、Git 和最终交付。

项目负责人和全部十一个专项员工永久统一使用 `GPT-5.6 Terra 高 / high`。仓库配置不能强制平台实际分配；出现不一致时必须如实报告。

## 协作规则

1. 接手后先调用 RequirementCertifier 做初审。
2. 缺口优先由 CodeExplorer、KnowledgeExpert 和 UIReferenceAnalyst 从本地文档、两个案例和当前代码中解决。
3. 只有不可推导且会明显影响产品、安全、兼容性或验收的选择才询问用户。
4. 实施前再次调用 RequirementCertifier；没有 READY 不写代码。
5. TestEngineer、RealtimeChecker、DocUpdater、ProjectManager、AntiHallucination、ReleaseManager、Handover 按固定检查点依次完成验证、记录、提交和交接。

## 防幻觉与拆分

AntiHallucination 已完成两次检查：初稿检查 9 个文件，提交前终检覆盖 14 个新增/大改文件。最长文件 192 行，项目负责人配置 154 行；全部职责单一且低于 500 行，不需要拆分。

未来文件超过 500 行时先生成拆分报告；只有职责混杂并取得独立重构 READY 后才能拆分。原文件保留稳定入口，详细内容放回同一功能目录。

## Git、测试与边界

- v019 基线：`02536f7`，远端分支和标签均存在。
- v020.1/v020.2：`546d899`、`06bef74` 已推送。
- 16 项单元测试通过，Python 编译通过，`git diff --check` 通过。
- 本轮只改文档和 Agent 配置；没有修改 UI、Python 运行代码、依赖、F9/F12/F2 或 OSD。
- 两份优秀案例仍只读且未被 Git 跟踪。

## 下一位 AI

先读 `AGENTS.md`、`.codex/agents/1-project-lead.md` 和 `CURRENT_HANDOVER.md`。下一项候选任务是 v021 Quickinput 四页 UI 外壳，但当前仍为 NOT READY；必须先由团队用本地证据关闭剩余技术项，再由 RequirementCertifier 终审。

下一份历史交接使用 `3-` 前缀，不得覆盖本文件。
