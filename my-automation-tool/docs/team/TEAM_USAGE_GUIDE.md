# 团队使用教程（小白版）

## 启动项目

```powershell
cd C:\Users\s\Desktop\1-test\1-自动连点器\my-automation-tool
python main.py
```

## 如何叫团队工作

你只需对总负责人这样说：

- “让 DocUpdater 更新文档。”
- “让 CodeExplorer 查找 F9 的执行逻辑。”
- “让 KnowledgeExpert 在优秀案例中找热键方案。”
- “让 RealtimeChecker 检查这次改动是否偏离 Quickinput。”
- “让 TestEngineer 给我准备人工测试教程。”
- “让 Handover 写给下一位 AI 的交接。”

总负责人会读取 `.codex/agents/` 对应角色规范并派发任务。优秀案例不会上传或提交，只在本机查阅。

## 你需要人工测试的节点

| 节点 | 你要做什么 | 通过标准 |
|---|---|---|
| 修改 F9/F12、输入或播放器 | 依 `USER_TEST_GUIDE.md` 用记事本测试 | F12 红绿 OSD 正确；F9 输出符合模式；停止后无后续输入 |
| 新 UI 外壳 | 对照 `docs/reference/quickinput-ui/` 截图 | 四页外观、禁用控件和 F2 占位符合规格 |
| 新宏库/多脚本功能 | 按 TestEngineer 提供教程 | 新脚本、热键和停止行为均可重复验证 |

在通知你测试前，团队必须先运行自动测试和语法检查；你只需报告“按了什么、看到什么”。
