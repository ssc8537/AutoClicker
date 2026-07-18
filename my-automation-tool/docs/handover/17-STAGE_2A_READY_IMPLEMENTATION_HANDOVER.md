# 17 - 给下一位 AI 工作 - Stage 2A READY 实施交接

> 日期：2026-07-17
>
> Git：工作区含既有未提交改动；未提交、未推送。

## 就绪结论

Stage 1 Windows 人工验收已由用户确认 1–9 全部通过。RequirementCertifier 对 Stage 2A 给出 **READY（受限）**。

## 唯一允许实现

- Python 宏新建、重命名、内置编辑、原子保存、重新加载。
- UTF-8 `.py` 宏持续静态满足 `NAME/HOTKEY/MODE/COUNT/SPEED` 和严格 `run(player)`。
- 保存失败不得覆盖旧文件；活动宏必须先在触发页禁用才可重命名。

## 禁止实现

导入、导出、删除、触发配置或自定义快捷键、多宏、鼠标、录制。F9/F12、F2、OSD、Candy UI、唯一活动宏和 fail-closed 不得改变。
