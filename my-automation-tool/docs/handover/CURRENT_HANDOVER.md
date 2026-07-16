# 下一位 AI：当前交接（v021.1 已发布）

## 第一身份与强制步骤

主要 Agent 必须先读取根目录 `AGENTS.md` 和 `.codex/agents/1-project-lead.md`，以“项目负责人”身份接手。第一个员工必须调用 GoalAlignmentMonitor（总目标对齐监控员），第二个员工必须调用 RequirementCertifier；前者为 `ALIGNED/DRIFT/UNKNOWN`，后者为 `READY/NOT READY`。两道门都不得跳过；没有实施前 `READY`，不得写代码、改运行配置、重构或进入新阶段。

项目负责人和全部专项员工永久统一使用 `GPT-5.6 Terra 高 / high`。项目文件不能强制平台实际模型；发现运行分配不一致时必须如实报告。

## Git 与已验收基线

- GitHub：`https://github.com/ssc8537/AutoClicker.git`。
- 当前分支：`codex/v021-ui-shell`。
- v019 阶段 3 基线：分支与标签均解析到 `02536f7`。
- v020 团队/UI 规格：远端原提交 `b04728e`。
- v020.1/v020.2：`546d899`、`06bef74` 已快进推送 GitHub。
- v020.3 项目负责人及团队协作闭环：`bab26c3`，已推送 GitHub。
- v021.1 UI 外壳与 V022 交接：`bc06485`，已安全快进发布至 `codex/v021-ui-shell` 和 GitHub 默认分支 `master`；禁止强推。
- 两份优秀案例只读、Git 忽略，禁止复制或提交源码。

## v020.3 完成内容

- 新增 `.codex/agents/1-project-lead.md`，作为唯一项目总入口。
- 团队共 13 个角色：项目负责人和十二个专项员工（含最高优先级 GoalAlignmentMonitor）；唯一职责见 `.codex/agents/README.md`。
- RequirementCertifier 分为接手初审和实施前终审。初审缺口先由团队查文档、案例、代码、测试和日志，不能直接全部询问用户。
- Handover 使用递增编号；本轮历史交接为 `4-V022_ROADMAP_GOVERNANCE_HANDOVER.md`，下一编号从 `5-` 开始。
- AntiHallucination 在初稿、提交前、重大里程碑和交接前检查新增/大改文件；超过 500 行且职责混杂时才提出拆分，并须另获重构 READY。

## 需求与运行边界

- 当前运行格式是可信本地 Python，不恢复 JSON/QIM。
- F9 运行 Python 宏，F12 是唯一实际全局开关；F2 仅 UI 占位。
- 已验收能力包括 F9/F12、OSD、`switch/down`、COUNT/SPEED、热重载、可中断播放和停止释放。
- 未开发功能只能显示为禁用或“后续阶段”，不得伪装为可用。
- 两份案例只用于查证设计；不引入图像识别、角色 AI、窗口匹配、录制、音效、鼠标执行或案例资产。

## 当前需求信心状态

团队治理和项目负责人任务：**READY，已完成。**

Quickinput 四页 UI 外壳：RequirementCertifier READY、实现、自动验证和用户运行/安全验收均已完成。用户认可 Candy 粉红色与 F9/F12/F2 安全回归，但整体视觉只部分认可。V022 视觉规格与用户确认清单已产出，当前等待用户确认；不直接改 UI 或扩展功能。

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
- 用户已确认外观/只读状态无 bug、F9/F12/F2 安全回归正常；视觉设计仍需 V022 对齐。不得把“运行验收通过”写成“视觉最终验收通过”。

## 必读顺序

1. `AGENTS.md`、`.codex/agents/1-project-lead.md`。
2. `PROJECT_OUTLINE.md`、`REVIEW_LOG.md`、`PROJECT_STRUCTURE.md`。
3. 本文件、`docs/requirements/CURRENT_PRODUCT_DECISIONS.md`、`V021_UI_SHELL_ACCEPTANCE_SPEC.md`。
4. `docs/reference/QUICKINPUT_UI_REFERENCE_SPEC.md` 和两个案例架构索引。
5. `.codex/agents/README.md` 及任务对应员工配置。

## 下一项唯一候选任务

V022：优秀案例 1 视觉与窗口规则对齐审查已完成规格，等待 `my-automation-tool/docs/test-plans/V022_VISUAL_SPEC_CONFIRMATION.md` 的用户确认。窗口最小高度继续保持 510，鼠标等功能仅灰置占位；任何后续实现都不得改变 F9、F12、F2、OSD 或输入行为，且必须重新获得 UI 实施 READY。

阶段路线图已审查并纠偏：有效主线、历史 JSON 基线和候选扩展见 `my-automation-tool/docs/requirements/ROADMAP_ALIGNMENT_AUDIT.md`。不得把 Quickinput 的窗口匹配、音效、录制、鼠标、多脚本或 JSON/QIM 误写为当前承诺。

## 本轮治理审查与归档（2026-07-16）

- GoalAlignmentMonitor 首次结论为 **DRIFT**：核心 Python-only、F9/F12、F2 占位、Candy UI 和案例只读边界未发现实现偏离；但旧交接仍把 RequirementCertifier 写为第一员工，且本轮审查/路线图草稿尚未归档。调用顺序现已更正为“GoalAlignmentMonitor 第一、RequirementCertifier 第二”；第三次复审为 **ALIGNED**，确认阶段分层、音效候选状态、UTF-8 角色配置和归档事实一致。
- 最终完整项目的扩展范围为 **UNKNOWN**：多 Python 宏、每宏热键、编辑/持久化、窗口、音效、鼠标、录制与定时尚未由用户锁定，均只能保留为候选，不能宣称“旧阶段全部完成即可交付完整项目”。
- RequirementCertifier：路线图/V022/GitHub SOP 的文档与角色配置范围最终为 **READY**，允许本轮提交；此前因最终 ALIGNED 未归档产生的 **NOT READY** 已纠正。UI、宏库与候选扩展代码均 **NOT READY**。V022 用户确认前不改 UI。
- AntiHallucination 首轮为 **NOT PASS**：发现 READY/完成状态在日志归档前被提前写入。日志、稳定交接与编号快照现已补齐；提交前必须再次复查才可提交。
- `0-goal-alignment-monitor.md` 已用 UTF-8 直接读取确认内容与模型字段正常；先前关于乱码的报告未被本地证据证实，提交前仍由 AntiHallucination 复核。
- 本轮治理、路线图、V022 规格和角色配置在此归档记录形成时仍未提交；已完成终检、路径和结构复核。ReleaseManager 必须先核对暂存范围仅含文档/角色配置，再提交并按 GitHub SOP 推送功能分支与 `master`；下一位 AI 不能根据本文假定远端已经包含本轮草稿。
