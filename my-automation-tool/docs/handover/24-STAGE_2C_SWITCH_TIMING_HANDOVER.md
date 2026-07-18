# 24 - 给下一位 AI 工作 - Stage 2C-S 三角色切人规则

> 日期：2026-07-17
>
> Git：工作区含既有未提交改动与本轮变更；未提交、未推送。

## 已完成

用户已确认 Stage 2C-R 人工验收通过。Stage 2C-S 只更新纯文本 AI 提示词、作者手册、路线文字和提示词治理规则，不改变运行时。提示词有三名角色名称填写区；AI 必须写角色编号注释，但切人仍仅用数字 `player.tap("1")`、`player.tap("2")`、`player.tap("3")`。

全部不同角色方向共用规则：切换前至少 `player.sleep(60)`；刚 A→B 后的 B→A 回切，从成功切到 B 起至少等待 `player.sleep(1100)`。1100ms 由 1000ms 冷却和 100ms 安全余量组成。Q 为声骸技能，R 为大招；鼠标和语义 API 均未发布。

## 验证与唯一用户动作

- 自动测试覆盖角色名称、六个方向、60ms/1100ms、数字键不变、注释要求、复制和既有热键回归。
- 完整回归、编译和 `git diff --check` 完成后，用户仅按 `../test-plans/STAGE_2C_SWITCH_TIMING_MANUAL_TEST.md` 做 Windows 文本验收。

## 后续边界

用户通过前只修复教程可复现的问题。通过后进入 Stage 2D 的独立 READY 门槛：触发页序号、隐藏 `.py`、全列居中。Stage 3K/3M、Stage 4T 和代码清理仍未 READY。
