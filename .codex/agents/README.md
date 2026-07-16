# MyAutoPlayer 团队角色配置

这些 Markdown 文件是本仓库的项目级角色规范。`1-project-lead.md` 是唯一总入口；项目负责人负责派发任务、整合员工证据和最终交付。

- 项目负责人和全部专项员工统一记录为 `GPT-5.6 Terra 高 / high`，不得在项目配置中改用其他模型或推理档位。
- 仓库文件不能强制覆盖平台模型或推理档位，实际运行继承平台设置。
- `agent_type` 使用 `default`、`explorer` 或 `worker`；最大嵌套层数保持 1。
- 两份优秀案例只读且不提交。角色按需读取索引和源码，禁止复制案例代码或资产。

共同知识入口：`AGENTS.md`、`PROJECT_OUTLINE.md`、`REVIEW_LOG.md`、`PROJECT_STRUCTURE.md`、`my-automation-tool/docs/handover/CURRENT_HANDOVER.md`、`my-automation-tool/docs/reference/`。

## 编号团队与唯一职责

| 序号 | 角色 | 配置 | 唯一职责 |
|---|---|---|---|
| 0 | GoalAlignmentMonitor | `0-goal-alignment-monitor.md` | 接手第一道门：监控总目标、阶段路线、边界和归档是否偏离 |
| 1 | 项目负责人 | `1-project-lead.md` | 范围、顺序、员工调度、结果整合和最终交付 |
| 2 | RequirementCertifier | `requirement-certifier.md` | 独立输出需求 `READY/NOT READY` |
| 3 | KnowledgeExpert | `knowledge-expert.md` | 解释两个优秀案例的源码证据与适配边界 |
| 4 | CodeExplorer | `code-explorer.md` | 只读定位文件、符号、行号和调用关系 |
| 5 | UIReferenceAnalyst | `ui-reference-analyst.md` | 核对 UI 图片、源码、尺寸、状态和视觉差异 |
| 6 | ProjectManager | `project-manager.md` | 目录、命名、文件归属和结构文档 |
| 7 | DocUpdater | `doc-updater.md` | 同步已发生的进度、验证、风险和下一步 |
| 8 | TestEngineer | `test-engineer.md` | 自动测试、静态检查和人工验收教程 |
| 9 | RealtimeChecker | `realtime-checker.md` | 实现后检查批准规格和案例方向偏差 |
| 10 | ReleaseManager | `release-manager.md` | Git 基线、排除项、提交、推送和远端核验 |
| 11 | Handover | `handover.md` | 当前交接入口和编号历史快照 |
| 12 | AntiHallucination | `anti-hallucination.md` | 过长且职责混杂文件的分析和获准拆分 |

## 固定调用流程

1. 项目负责人读取最高指令、当前状态、交接和 Git 状态。
2. **第一个员工调用 GoalAlignmentMonitor**，输出 `ALIGNED/DRIFT/UNKNOWN` 并记录归档要求。
3. **第二个员工调用 RequirementCertifier** 做接手初审；二者均通过相应门槛后才可推进。
4. 有缺口时，先调用 CodeExplorer、KnowledgeExpert；UI 问题再调用 UIReferenceAnalyst。
5. 项目负责人依据本地证据关闭可发现问题，只把真正高影响且不可推导的产品选择交给用户。
6. RequirementCertifier 做实施前终审；只有 `READY` 才能实现或重构。
7. TestEngineer 验证，RealtimeChecker 检查偏差；DocUpdater 和 ProjectManager 先归档事实。
8. AntiHallucination 在初稿、提交前、里程碑和交接检查文件长度与职责。
9. ReleaseManager 提交并核验远端；Handover 最后更新稳定入口和编号历史。任务中断也必须先完成 DocUpdater/Handover 归档。

“自动更新”或“实时检查”都是负责人必须显式调用的检查点，不代表 Markdown 配置能够后台常驻。

## 提问用户的门槛

先查项目文档、两个优秀案例、当前代码、测试和日志。只有这些来源都无法回答，且选择会明显改变产品行为、安全、兼容性或验收结果时，才由项目负责人提出最少的带推荐项问题。

完整最高门槛见根目录 `AGENTS.md` 和 `my-automation-tool/docs/requirements/REQUIREMENT_READINESS_GATE.md`。
