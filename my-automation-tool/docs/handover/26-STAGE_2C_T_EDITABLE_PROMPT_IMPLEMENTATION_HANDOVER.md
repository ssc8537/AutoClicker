# Stage 2C-T 可编辑提示词文件实施交接

日期：2026-07-18  
状态：自动检查完成；Windows 人工验收待进行  
Git：工作区已有用户未提交改动；本轮未提交、未推送

## 已完成

- 新增 `config/ai_prompt.txt`，所有作者和使用者可直接用记事本编辑；新增 `config/ai_prompt.default.txt`，程序绝不自动改写它。
- 提示词窗口每次重新打开时读取当前文件，显示当前文件与默认备份的绝对路径和人工恢复说明。
- 仅在当前文件缺失时用默认备份恢复；当前文件 UTF-8/读取失败时不覆盖，改为安全显示默认文本；两个文件均不可读时显示安全提示且不崩溃。
- 有效宏仍仅读取已保存源码并附加到提示词末尾，绝不导入、执行或写入宏源码。
- 默认模板、作者手册和示例新增 R 后 `player.sleep(1800)`：这是一条作者保守时序规则，覆盖普通切人 60ms 与回切 1100ms；之后可直接发任一其他数字槽位。程序不识别动画、不检测 CD、不提供角色语义 API。

## 自动检查

在 `my-automation-tool` 执行：

- `python -m unittest discover -s tests -v`：41/41 通过。
- `python -m compileall -q main.py src macros`：通过。
- `git diff --check`：通过；仅有既有工作区文件的 CRLF 警告。

测试覆盖首次恢复、外部编辑后重开、路径、复制、缺失恢复、乱码不覆盖、双文件不可读、默认备份不改写、有效/无效宏源码附带、R 后 1800ms 和 F9/F12 回归。

## 仍需用户操作

按 `../test-plans/STAGE_2C_EDITABLE_PROMPT_MANUAL_TEST.md` 做 Windows 验收。未启动真实 GUI、未发送真实输入，不能把自动检查当作人工验收。通过前只修复该教程可复现的问题；不得进入 Stage 2D、鼠标、键位配置、角色/技能语义 API、多宏或新热键。

## 本次审查与恢复入口

GoalAlignmentMonitor：初检 `DRIFT`（Stage 2C-S 已通过却仍写待验收），归档后 `ALIGNED`。RequirementCertifier：`READY（仅 Stage 2C-T，受限）`。AntiHallucination 初审发现“实现已存在、稳定文档仍称未实施”的状态冲突，已在稳定入口更正；文件均不超过 500 行，无需拆分。

下一位 AI 先读 `CURRENT_HANDOVER.md`、本文件、`REVIEW_LOG.md`、`CURRENT_PRODUCT_DECISIONS.md`、`STAGE_2C_EDITABLE_PROMPT_MANUAL_TEST.md`。用户确认 Windows 验收后，先归档 Stage 2C-T；未得到新 READY 不进入 Stage 2D。
