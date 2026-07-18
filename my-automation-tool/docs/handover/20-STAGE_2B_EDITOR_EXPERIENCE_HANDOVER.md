# 20 - 给下一位 AI 工作 - Stage 2B 编辑体验实施交接

> 日期：2026-07-17
>
> Git：工作区含既有未提交改动与本轮变更；未提交、未推送。

## 已实现

- 宏列表显示文件名主体而非 `.py`；无效宏继续只显示为红字。
- 单击仅选中脚本；右侧名称框 Enter 与“保存”复用既有原子重命名事务。
- 新建和编辑窗口的按钮固定中文“保存”“取消”。
- 新增本项目自有 Python 高亮器和编辑区：关键字、字符串、注释、数字、函数定义使用彩色显示；Tab 插入四个空格，选中多行时逐行缩进。

## 验证与当前唯一任务

- `python -m unittest discover -s tests -v`：**39/39 通过**。
- `python -m compileall -q main.py src macros`、`git diff --check`：通过。
- 用户按 `../test-plans/STAGE_2B_EDITOR_EXPERIENCE_MANUAL_TEST.md` 完成 Windows 验收；通过前仅修复该教程可复现的问题。

## 后续边界

Stage 3K 全局游戏键位和 Stage 3M 鼠标尚未 READY，路线见 `../requirements/GAME_AUTHORING_ROADMAP.md`。不得提前改变 F9/F12/F2、唯一活动宏、AST 静态校验、原子保存、OSD 或真实输入链路。
