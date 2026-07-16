# 3-给下一位AI工作-V021验收反馈与UI视觉对齐

## 当前状态

- 当前分支：`codex/v021-ui-shell`。
- 当前实现提交：`9af65c9`（`v021 - 四页UI外壳与人工验收`）。
- v021 已完成 Candy 粉红四页 UI 外壳；F9 运行 Python 宏、F12 全局开关、F2 仅占位，OSD 与退出清理保持原有行为。
- 自动验证通过：23/23 单元测试、Python 编译、离屏 UI 截图和 `git diff --check`。
- 用户已确认：只读状态、F9/F12/F2 和安全回归正常；喜欢粉红主题。整体视觉设计只部分认可，不能宣称视觉最终验收通过。

## 用户最新决定

- 继续保留 Candy 粉红方向，并在优秀案例 1 的源码与图片基础上提高 UI 精致度。
- 功能与逻辑继续遵循已锁定需求和优秀案例 1；二者与用户临时想法冲突时，优先优秀案例 1。
- 鼠标执行、快速鼠标点击等未开发能力只能灰置占位，禁止注册热键、执行输入或伪装为可用。
- 四张原始参考图位于 `my-automation-tool/优秀案例1-Quickinput/1-UI图片/`；项目提交副本位于 `my-automation-tool/docs/reference/quickinput-ui/`。
- 用户提出窗口可缩到半高，但同时指定优秀案例 1 优先。案例 `MainUi.ui` 最小高度为 510；当前保留 510，未取得新的 READY 前禁止改成半高裁切。

## 最高规则与必读顺序

1. `AGENTS.md`、`.codex/agents/1-project-lead.md`。
2. `PROJECT_OUTLINE.md`、`REVIEW_LOG.md`、`PROJECT_STRUCTURE.md`。
3. `docs/handover/CURRENT_HANDOVER.md`、本文件。
4. `docs/requirements/CURRENT_PRODUCT_DECISIONS.md`、`V021_UI_SHELL_ACCEPTANCE_SPEC.md`。
5. `docs/reference/QUICKINPUT_UI_REFERENCE_SPEC.md`、`QUICKINPUT_ARCHITECTURE_REFERENCE.md`、四张原始图片和案例 UI 源码。
6. `.codex/agents/requirement-certifier.md`、`knowledge-expert.md`、`ui-reference-analyst.md`、`code-explorer.md`。

所有负责人和员工目标配置统一为 `GPT-5.6 Terra 高 / high`。写代码、改窗口规则或进入新阶段前，先调用 RequirementCertifier；案例与当前项目资料能回答的问题不得交给用户。

## 下一项唯一任务

**V022：优秀案例 1 视觉与窗口规则对齐审查，不写 UI 代码。**

1. RequirementCertifier 做接手初审。
2. KnowledgeExpert 重新核对案例窗口尺寸、最小高度、缩放限制和布局源码。
3. UIReferenceAnalyst 逐张比对四张原图、当前 v021 截图和现有 UI 规格，输出“保留 / 调整 / 占位”清单。
4. CodeExplorer 定位当前窗口约束、样式和控件行号。
5. 写出 V022 可执行视觉规格：颜色、字体、间距、页面层级、按钮状态、窗口最小高度与裁切规则。
6. RequirementCertifier 实施前终审为 READY 后，才允许新的 UI 调整。

提交前必须再次调用 TestEngineer、RealtimeChecker、AntiHallucination、ProjectManager、DocUpdater 和 Handover。禁止直接改最小高度，禁止新增鼠标执行，禁止修改 F9/F12/F2/OSD，禁止复制案例资源。
