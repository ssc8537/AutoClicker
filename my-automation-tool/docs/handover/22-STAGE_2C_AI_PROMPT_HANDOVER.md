# 22 - 给下一位 AI 工作 - Stage 2C AI 提示词

> 日期：2026-07-17
>
> Git：工作区含既有未提交改动与本轮变更；未提交、未推送。

## 已完成

用户已通过 Stage 2B-R。RequirementCertifier 对 Stage 2C 给出 **READY（受限）**；宏页现有“编辑”下方新增始终可用的“AI 提示词”。窗口中的文本只读，可复制到剪贴板；有效选中宏只调用既有 `MacroFileManager.read_source()` 读取已保存源码，读取失败、无效或未选中均退回通用模板，绝不执行宏。

模板只允许 `player.tap(key, hold_ms=20)` 和 `player.sleep(ms)`，要求保留 `NAME/HOTKEY/MODE/COUNT/SPEED` 与 `run(player)` 并返回完整 Python 文件。禁止鼠标、角色/技能语义、F9/F12/F2 改动、图像识别和案例角色 AI。

## 验证与唯一用户动作

- `python -m unittest discover -s tests -v`：**40/40 通过**。
- `python -m compileall -q main.py src macros`、`git diff --check`：通过。
- 用户仅按 `../test-plans/STAGE_2C_AI_PROMPT_MANUAL_TEST.md` 做 Windows 剪贴板与 F9/F12 回归验收。

## 后续边界

用户通过前只修复该教程可复现的问题。之后才可独立审查 Stage 2D 触发页的序号、无后缀与居中；Stage 3K/3M、Stage 4T 系统托盘和 `macro_library.py` 清理仍未 READY。
