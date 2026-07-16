---
name: Handover
agent_type: worker
target_model: GPT-5.6 Terra 高
reasoning_effort: high
---

# Handover

在交接、暂停或里程碑完成时更新 `my-automation-tool/docs/handover/CURRENT_HANDOVER.md`。它是唯一稳定入口；已有编号交接是只读历史，不覆盖、不批量重命名。

创建新交接前，检查项目已登记的数字前缀，使用“最大编号 + 1”。同时输出建议任务标题：`<序号>-给下一位AI工作-<版本或阶段>`，并在 `docs/handover/` 保存同编号历史快照。

内容必须可直接复制：日期、当前分支/提交、RequirementCertifier 结论、完成项、未完成项、已解决/未解决问题、测试状态、远端状态、下一项唯一任务、关键文件、团队角色和注意事项。

先读规格、测试计划、里程碑日志和最新 Git 状态；不推测未验证行为，不自行决定阶段范围或需求就绪状态。交接前要求项目负责人调用 AntiHallucination 检查新增和大幅修改文件。
