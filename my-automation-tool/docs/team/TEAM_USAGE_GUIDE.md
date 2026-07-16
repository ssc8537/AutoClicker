# 团队使用教程（小白版）

## 启动项目

```powershell
cd C:\Users\s\Desktop\1-test\1-自动连点器\my-automation-tool
python main.py
```

## 如何叫团队工作

你可以直接说：“让项目负责人接手并继续当前唯一任务。”项目负责人会先做需求信心审查，再安排员工。

需要指定员工时，可以这样说：

- “让 DocUpdater 更新文档。”
- “让 CodeExplorer 查找 F9 的执行逻辑。”
- “让 KnowledgeExpert 在优秀案例中找热键方案。”
- “让 RealtimeChecker 检查这次改动是否偏离 Quickinput。”
- “让 TestEngineer 给我准备人工测试教程。”
- “让 Handover 写给下一位 AI 的交接。”
- “让 RequirementCertifier 审查这个需求是否已经可以写代码。”
- “让 AntiHallucination 检查新增文件是否超过 500 行且职责混杂。”

项目负责人配置位于 `.codex/agents/1-project-lead.md`。它会读取对应员工规范并派发任务；优秀案例不会上传或提交，只在本机查阅。

项目负责人和全部员工的目标配置永久统一为 `GPT-5.6 Terra 高 / high`。项目文件不能强制平台实际分配模型；如果平台显示不一致，负责人必须直接告诉你，不能假装已经切换。

每次新功能或修改开始前，RequirementCertifier 必须给出 `READY`；如果是 `NOT READY`，团队只会完善需求文档，不会开始写代码。这是本项目的最高工作门槛。

项目负责人不会把源码中能够查明的事实交给你决定。它会先查项目文档、优秀案例、代码、测试和日志；只有确实无法推导且会明显影响产品结果的问题才询问你。

## 固定协作顺序

1. RequirementCertifier 做接手初审。
2. KnowledgeExpert、CodeExplorer 和需要时的 UIReferenceAnalyst 查本地证据。
3. 项目负责人自行关闭技术细节，RequirementCertifier 再做实施前终审。
4. `READY` 后才实现；TestEngineer 和 RealtimeChecker 负责复核。
5. AntiHallucination 在初稿、提交前、里程碑和交接检查过长文件。
6. ReleaseManager 推送 GitHub，Handover 更新当前与编号交接。

这些员工由项目负责人显式调用，不是后台自动程序。

## 你需要人工测试的节点

| 节点 | 你要做什么 | 通过标准 |
|---|---|---|
| 修改 F9/F12、输入或播放器 | 依 `USER_TEST_GUIDE.md` 用记事本测试 | F12 红绿 OSD 正确；F9 输出符合模式；停止后无后续输入 |
| 新 UI 外壳 | 对照 `docs/reference/quickinput-ui/` 截图 | 四页外观、禁用控件和 F2 占位符合规格 |
| 新宏库/多脚本功能 | 按 TestEngineer 提供教程 | 新脚本、热键和停止行为均可重复验证 |

在通知你测试前，团队必须先运行自动测试和语法检查；你只需报告“按了什么、看到什么”。
