# 18 - 给下一位 AI 工作 - Stage 2A Python 宏文件管理实施交接

> 日期：2026-07-17
>
> Git：工作区包含既有未提交改动与本轮 Stage 2A；未提交、未推送。

## 已实现

- 宏页右栏新增新建、编辑、保存名称/重命名、重新加载；删除仍禁用。
- 内置编辑器编辑可信本地 UTF-8 Python 文件；新建模板和保存结果必须静态包含 `NAME/HOTKEY/MODE/COUNT/SPEED` 与严格 `run(player)`。
- 保存先写入同目录临时文件、再次静态校验后原子替换；语法、元数据、签名或写入失败都不会覆盖旧文件。
- 重命名同步文件名与 `NAME`；非法 Windows 名称、大小写冲突、同名目标和活动宏编辑/重命名都会拒绝。
- 重新加载只扫描和刷新列表，绝不执行宏顶层代码。

## 验证与当前唯一任务

- `python -m unittest discover -s tests -v`：34/34 通过。
- `python -m compileall -q main.py src macros`、`git diff --check`：通过。
- 用户需要按 `../test-plans/STAGE_2A_PYTHON_MACRO_MANAGEMENT_MANUAL_TEST.md` 做 Windows 验收。

用户通过前只修复教程可复现的 Stage 2A 问题。不得进入 Stage 2B、触发配置、可配置快捷键、多宏、鼠标或录制。
