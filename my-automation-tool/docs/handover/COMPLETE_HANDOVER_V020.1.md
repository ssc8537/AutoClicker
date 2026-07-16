# 完整交接：v020.1 / v021 前

## Git 与安全基线

- 工作目录：`C:\Users\s\Desktop\1-test\1-自动连点器`
- 当前分支：`codex/v020-team-ui-spec`
- 可回退基线：`codex/v019-stage3-accepted-baseline`，提交 `02536f7`，同名 Git 标签已推送。
- 两份案例目录只读且 Git 忽略，禁止提交或复制源码：`my-automation-tool/优秀案例1-Quickinput/`、`my-automation-tool/优秀案例2-okww/`。

## 已实现且已验收的运行能力

- Python 是唯一运行宏格式；JSON/QIM 只可作为历史资料。
- F12 为全局启用/禁用；F9 运行 `scripts/hello_world.py`。
- 只支持 `switch/down`；`COUNT=0` 的 down 在松开 F9 时停止；F2 仅 UI 占位。
- 有 OSD、热重载、可中断 `tap/sleep`、按键释放保护和单实例播放器。
- v019 提交前已复跑 16 项自动测试和 Python 编译；真实输入只能由用户手动在记事本验收。

## 每位负责人必须先做的事

1. 读根目录 `AGENTS.md`。
2. 调用 `.codex/agents/requirement-certifier.md`。
3. 按 `docs/requirements/REQUIREMENT_READINESS_GATE.md` 输出 READY 或 NOT READY，并记录在 `REVIEW_LOG.md` 和当前交接文档。
4. NOT READY 时只能研究案例、完善需求文档和询问用户；禁止写代码、修改 UI 运行代码或改变 F9/F12/OSD。

“100% 信心”定义为清单项均有证据且无阻塞未决项，不是没有 bug 的主观承诺。

## 当前唯一候选任务：四页 UI 外壳

状态：**NOT READY，禁止编码。**

已锁定：Quickinput 红库方向；宏库、触发、功能、设置四页；F9/F12/OSD 不回归；F2 只占位；宏库只读展示 `hello_world.py`；触发只读展示 F9/MODE/COUNT/SPEED；设置页只展示 F12/OSD；功能页可显示快速鼠标点击开关等原版外观但全部灰置并标“后续阶段”。不做鼠标执行、窗口匹配、录制、音效、定时、OCR、多脚本、任意热键或 Python 写回。

KnowledgeExpert 已从 Quickinput 核对窗口规则：默认 642×510、宽固定 642、最小高 510、最大高为主屏高度、仅纵向缩放、恢复有效已保存尺寸并居中、默认页索引 0。证据在 `MainUi.ui:5-29,281-311`、`MainUi.cpp:10-18,21-34,152-155`、`type.cpp:51-52,223`。无证据证明最后页面记忆，因此本阶段不保存页面。

## 仍需关闭的阻塞项

查看 `docs/requirements/V021_UI_SHELL_ACCEPTANCE_SPEC.md`：视觉验收尺度、只读控件是否允许无副作用选中、UI 测试技术和截图通过标准。得到用户答案后，重新调用 RequirementCertifier；只有 READY 才能开始。

## 必读路径

- 最高指令：`AGENTS.md`
- 当前产品决定：`docs/requirements/CURRENT_PRODUCT_DECISIONS.md`
- v021 规格：`docs/requirements/V021_UI_SHELL_ACCEPTANCE_SPEC.md`
- UI 源码规格：`docs/reference/QUICKINPUT_UI_REFERENCE_SPEC.md`
- 案例索引：`docs/reference/QUICKINPUT_ARCHITECTURE_REFERENCE.md`、`OK_WW_INPUT_ARCHITECTURE_REFERENCE.md`
- 团队角色：`.codex/agents/README.md`
- 当前测试：`docs/USER_TEST_GUIDE.md`、`tests/`
