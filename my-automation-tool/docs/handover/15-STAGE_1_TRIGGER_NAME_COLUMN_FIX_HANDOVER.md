# 15 - 给下一位 AI 工作 - Stage 1 触发页名称列修复交接

> 日期：2026-07-17
>
> Git：工作区含既有未提交改动；本轮未提交、未推送。

## 用户实测与已修复问题

用户确认 Stage 1 的宏页选择、无校验/错误效果、触发页全量四列和右侧只读栏均正确。唯一问题有 Windows 截图：触发表点击或 F9 后会横向偏移，隐藏“名称”列。

`main.py` 已将右侧触发详情栏固定为窄栏，并缩小前三列固定宽度；左表现在有足够宽度容纳四列。选中、点击及重绘都会把隐藏的横向滚动复位。`tests/test_ui_shell.py` 新增实际打开触发页后横向滚动范围和值必须为 0 的断言。

## 验证

- 离屏截图：四列均可见，选中后滚动为 `0/0`。
- `python -m unittest discover -s tests -p test_ui_shell.py -v`：9/9 通过。
- `python -m unittest discover -s tests -v`：29/29 通过。
- `python -m compileall -q main.py src macros`、`git diff --check`：通过。
- 单项等待时间测试一次为 74ms（阈值 60ms），完整复跑通过；属于既有 Windows 调度抖动，不是本轮 UI 缺陷。

## 唯一下一步

请用户在 Windows 中复查：点击触发表或按 F9 后，“名称、按键、模式、状态”是否始终同时可见。用户确认后，归档 Stage 1 人工验收并进入 Stage 2A 的 RequirementCertifier 审查；不得直接实现鼠标、触发配置或 Stage 2B。
