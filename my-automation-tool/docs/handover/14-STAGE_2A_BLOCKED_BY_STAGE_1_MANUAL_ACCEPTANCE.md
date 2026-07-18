# 14 - 给下一位 AI 工作 - Stage 2A 人工验收阻塞交接

> 日期：2026-07-17
>
> Git：工作区有既有未提交改动；本轮只更新归档文档，未提交、未推送。不得清理、回退或发布。

## 当前结论

用户已批准“鼠标宏分阶段扩展计划”，但 GoalAlignmentMonitor 结论为 **DRIFT**。原因不是用户目标不清楚，而是 Stage 1 的 Windows/记事本人工验收仍在稳定文档中标为待完成。按小阶段循环，未记录该验收通过前不得开始 Stage 2A，也不得调用 RequirementCertifier 审查 Stage 2A。

## 已锁定的后续路线

- Stage 2A：仅 Python 宏新建、重命名、内置编辑、原子保存、重新加载。
- Stage 2B：导入、导出、删除，独立进行。
- Stage 3：单宏触发配置；Stage 3M 才实现鼠标左/右键按下、释放、单击与有限连点。
- Python 是唯一宏格式；禁止 JSON/QIM、案例源码或资源复制。鼠标功能只能由触发页已启用宏的 `run(player)` 使用，未调用鼠标 API 的宏不得影响正常鼠标。

## 恢复入口

请用户明确确认已按 `../test-plans/STAGE_1_MACRO_OVERVIEW_MANUAL_TEST.md` 在 Windows/记事本完成并通过验收。之后由 RequirementCertifier 给出 Stage 2A 的 `READY/NOT READY`；只有 `READY` 才允许写代码。
