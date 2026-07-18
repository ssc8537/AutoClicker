# 23 - 给下一位 AI 工作 - Stage 2C-R 纯文本提示词

> 日期：2026-07-17
>
> Git：工作区含既有未提交改动与本轮变更；未提交、未推送。

## 已完成

用户已确认 Stage 2C 原始提示词复制验收通过。Stage 2C-R 仅修复该阶段反馈：`ai_prompt_dialog.py` 成为提示词和对话框的独立入口，提示词框架不再包含 Markdown 标题、列表或代码围栏；选中宏的原始源码仍逐字附带，源码自身注释保留。

提示词和 `docs/macro-authoring/AUTHORING_GUIDE.md` 均说明当前已发布的 `player.tap`、`player.sleep`、五项元数据、`run(player)` 与安全边界。最新键位参考固定为 E 战技、Q 声骸技能、R 大招；“小技能”已移除。鼠标和语义 API 仍未发布。

## 验证与唯一用户动作

- 自动专项测试覆盖纯文本框架、源码注释、Q/R 名称、只读复制和安全回退。
- 完整回归、编译和 `git diff --check` 完成后，用户仅按 `../test-plans/STAGE_2C_AI_PROMPT_MANUAL_TEST.md` 做 Windows 验收。

## 后续边界

用户通过前只修复此教程的可复现问题。随后才进入独立 Stage 2D 触发页修正；Stage 3K/3M、Stage 4T 和代码清理均未 READY。
