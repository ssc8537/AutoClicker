# MyAutoPlayer 团队角色配置

这些 Markdown 文件是本仓库的项目级角色规范。总负责人在派发任务前必须把对应文件、任务范围和必要的项目文档交给子 Agent。

- 目标模型与推理档位统一记录为 `GPT-5.6 Terra 高 / high`。
- 当前 Codex 运行时不允许由仓库文件强制覆盖模型或推理档位；实际子 Agent 继承平台设置。
- `agent_type` 使用 `default`、`explorer` 或 `worker`；最大嵌套层数保持 1。
- 两份优秀案例只读且不提交。角色按需读取索引和源码，禁止把案例代码复制进本项目。

共同知识入口：`my-automation-tool/docs/reference/`、`my-automation-tool/PROJECT_SPEC.md`、`PROJECT_STRUCTURE.md`。

**最高优先级：** 任何负责人接手或准备写代码前，必须先使用 `requirement-certifier.md`。完整门槛在根目录 `AGENTS.md` 和 `docs/requirements/REQUIREMENT_READINESS_GATE.md`。
