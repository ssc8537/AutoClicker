# 下一位 AI：当前交接（v020.3）

## 第一身份与强制步骤

主要 Agent 必须先读取根目录 `AGENTS.md` 和 `.codex/agents/1-project-lead.md`，以“项目负责人”身份接手。第一个员工调用必须是 RequirementCertifier；没有实施前 `READY`，不得写代码、改运行配置、重构或进入新阶段。

项目负责人和全部专项员工永久统一使用 `GPT-5.6 Terra 高 / high`。项目文件不能强制平台实际模型；发现运行分配不一致时必须如实报告。

## Git 与已验收基线

- GitHub：`https://github.com/ssc8537/AutoClicker.git`。
- 当前分支：`codex/v021-ui-shell`。
- v019 阶段 3 基线：分支与标签均解析到 `02536f7`。
- v020 团队/UI 规格：远端原提交 `b04728e`。
- v020.1/v020.2：`546d899`、`06bef74` 已快进推送 GitHub。
- v020.3 项目负责人及团队协作闭环：`bab26c3`，已推送 GitHub。
- v021 UI 外壳尚待本分支提交；禁止强推。
- 两份优秀案例只读、Git 忽略，禁止复制或提交源码。

## v020.3 完成内容

- 新增 `.codex/agents/1-project-lead.md`，作为唯一项目总入口。
- 团队共 12 个角色：项目负责人和十一个专项员工；唯一职责见 `.codex/agents/README.md`。
- RequirementCertifier 分为接手初审和实施前终审。初审缺口先由团队查文档、案例、代码、测试和日志，不能直接全部询问用户。
- Handover 使用递增编号；本轮历史交接是 `2-PROJECT_LEAD_GOVERNANCE_V020.3.md`，下一编号从 `3-` 开始。
- AntiHallucination 在初稿、提交前、重大里程碑和交接前检查新增/大改文件；超过 500 行且职责混杂时才提出拆分，并须另获重构 READY。

## 需求与运行边界

- 当前运行格式是可信本地 Python，不恢复 JSON/QIM。
- F9 运行 Python 宏，F12 是唯一实际全局开关；F2 仅 UI 占位。
- 已验收能力包括 F9/F12、OSD、`switch/down`、COUNT/SPEED、热重载、可中断播放和停止释放。
- 未开发功能只能显示为禁用或“后续阶段”，不得伪装为可用。
- 两份案例只用于查证设计；不引入图像识别、角色 AI、窗口匹配、录制、音效、鼠标执行或案例资产。

## 当前需求信心状态

团队治理和项目负责人任务：**READY，已完成。**

Quickinput 四页 UI 外壳：RequirementCertifier 实施前终审为 **READY**，实现和自动验证已完成。当前分支 `codex/v021-ui-shell` 已在 `MainWindow._setup_ui()` 加入 Candy 粉红四页外壳；F9/F12/OSD/播放器/F2 和真实输入边界未变。下一步只能等待用户记事本与视觉验收，不扩展功能。

## 验证结果

- `python -m unittest discover -s tests -v`：16/16 通过。
- `python -m compileall -q main.py src scripts`：通过。
- `git diff --check`：通过。
- AntiHallucination：初稿检查 9 个文件；提交前终检覆盖 14 个新增/大改文件，最长 192 行，项目负责人配置 154 行。无文件超过 500 行，无需拆分。
- 本轮未启动 GUI、未发送真实键盘或鼠标输入，无需用户人工测试。

## v021 自动验证与人工验收

- 23/23 单元测试、Python 编译、离屏截图和 `git diff --check` 通过。
- RealtimeChecker：未发现 F9/F12、播放器、OSD、关闭清理或真实输入路径偏离。
- AntiHallucination：PASS，`main.py` 434 行、UI 测试 79 行，均无需拆分。
- 用户必须执行 `docs/test-plans/V021_UI_SHELL_MANUAL_TEST.md`。通过前不得宣称 v021 已人工验收，也不得实现下一阶段功能。

## 必读顺序

1. `AGENTS.md`、`.codex/agents/1-project-lead.md`。
2. `PROJECT_OUTLINE.md`、`REVIEW_LOG.md`、`PROJECT_STRUCTURE.md`。
3. 本文件、`docs/requirements/CURRENT_PRODUCT_DECISIONS.md`、`V021_UI_SHELL_ACCEPTANCE_SPEC.md`。
4. `docs/reference/QUICKINPUT_UI_REFERENCE_SPEC.md` 和两个案例架构索引。
5. `.codex/agents/README.md` 及任务对应员工配置。

## 下一项唯一候选任务

由项目负责人组织 KnowledgeExpert、CodeExplorer 和 UIReferenceAnalyst，用优秀案例源码及现有规格自行关闭 v021 UI 的剩余技术项；只有 RequirementCertifier 给出实施前 READY 后，才允许制作四页 UI 外壳。任何实现都不得改变 F9、F12、F2、OSD 或输入行为。
