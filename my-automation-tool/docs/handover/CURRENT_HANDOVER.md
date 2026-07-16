# 下一位 AI：当前交接（v020）

## 当前完成情况

- v019 是已推送 GitHub 的阶段 3 可回退基线：`codex/v019-stage3-accepted-baseline` 和同名标签。
- 当前工作分支：`codex/v020-team-ui-spec`。本分支仅新增团队、案例和 UI 规格文档，不改变运行逻辑。
- 已验收运行能力：固定 F9 Python 宏、F12 全局开关、OSD、`switch/down`、`COUNT`、`SPEED`、热重载、可中断单实例播放器。
- 脚本格式为可信本地 Python；JSON 仅历史材料，绝不重新作为运行格式。

## 必读顺序

1. `README.md`、`PROJECT_STRUCTURE.md`、`my-automation-tool/PROJECT_SPEC.md`
2. `docs/reference/QUICKINPUT_UI_REFERENCE_SPEC.md`
3. `docs/reference/QUICKINPUT_ARCHITECTURE_REFERENCE.md`、`OK_WW_INPUT_ARCHITECTURE_REFERENCE.md`
4. `.codex/agents/README.md` 与任务对应的角色配置
5. `USER_TEST_GUIDE.md`、`REVIEW_LOG.md`、本文件

## 下一项唯一开发任务

做 Quickinput 风格的四页 UI 外壳和红库主题：宏库、触发、功能、设置。不得实现新的鼠标、窗口、录制、音效、定时、OCR、多脚本并发或自定义热键功能。

- F9、F12 和现有 OSD 必须继续运行。
- F2 仅显示预留位置，不能注册系统热键或改变 OSD。
- 功能页控件全部禁用或明确标“后续阶段”。
- 先自动回归，再让用户做视觉与 F9/F12 手动验收。

## 团队状态

十个角色配置位于 `.codex/agents/`；实际子 Agent 继承 Codex 平台模型设置。案例位于 `优秀案例1-Quickinput/`、`优秀案例2-okww/`，只读且 Git 忽略。
