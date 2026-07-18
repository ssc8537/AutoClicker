# Stage 2C-U 切人时序作者规则修订实施交接

日期：2026-07-18  
状态：自动检查完成；Windows 人工验收待进行  
Git：工作区已有未提交改动；本轮未提交、未推送

## 已完成

- 用户已确认 Stage 2C-T 教程 1–6 通过；历史教程与编号交接未改写。
- `config/ai_prompt.txt` 与 `config/ai_prompt.default.txt` 保持逐字一致；六个不同角色方向的普通切人均为至少 50ms。
- 回切规则为 1080ms，即 1000ms 冷却加 80ms 安全余量。
- R 规则为 `player.tap("R")` 后紧邻 `player.sleep(1500)`；它覆盖后续 50ms/1080ms 门槛，结束后可直接发其他 `1`/`2`/`3`。这是作者写法，不表示动画/CD/当前角色检测、角色语义 API 或自动输入。
- 作者手册、自动测试和 `../test-plans/STAGE_2C_U_SWITCH_TIMING_REVISION_MANUAL_TEST.md` 已同步；不改热键、真实输入、宏执行或 UI。

## 自动检查

在 `my-automation-tool` 执行：

- 独立模板规则检查：PASS（双模板一致、六方向、50ms/1080ms/1500ms、R 示例相邻且无额外等待）。
- `python -m unittest discover -s tests -v`：41/41 通过。
- `python -m compileall -q main.py src macros`：通过。
- `git diff --check`：通过；仅有既有工作区文件的 CRLF 警告。

未启动真实 GUI，未发送真实输入。提示词文件恢复、UTF-8 失败不覆盖、源码只读附带和 F9/F12 回归继续由既有测试覆盖。

AntiHallucination：PASS。两份模板各 47 行、作者手册 77 行、新教程 19 行、本交接 16 行；既有 `tests/test_ui_shell.py` 为 487 行但职责单一，无需拆分。Stage 2C-U 交付文件未残留 60ms/1100ms/1800ms 旧规则。

## 仍需用户操作

按 `../test-plans/STAGE_2C_U_SWITCH_TIMING_REVISION_MANUAL_TEST.md` 做 Windows 验收。通过前只修复该教程可复现问题；不得进入 Stage 2D、鼠标、键位配置、角色/技能语义 API、多宏或新热键。

## 恢复入口

先读 `CURRENT_HANDOVER.md`、本文件、`REVIEW_LOG.md`、`CURRENT_PRODUCT_DECISIONS.md` 和 Stage 2C-U 教程。用户确认后只归档本阶段验收结果；默认不提交、不推送。
