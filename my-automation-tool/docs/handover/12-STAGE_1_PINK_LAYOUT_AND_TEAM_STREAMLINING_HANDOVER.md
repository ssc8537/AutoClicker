# 12 - 给下一位 AI 工作 - 粉红双栏 UI 与员工精简交接

> 日期：2026-07-17
>
> Git：本地工作区有既有 C1/Stage 1 与本轮改动；均未提交、未推送。不得清理、回退或发布。

## 当前唯一任务

请让用户按 `../test-plans/STAGE_1_MACRO_OVERVIEW_MANUAL_TEST.md` 做 Windows/记事本人工验收。通过前只修复该教程能复现的本阶段 UI 或 F9/F12 回归问题；不得扩展功能。

## 已实现的 UI

- 保留 Candy 粉红主题与四页导航；只借鉴根目录 `2-UI图片` 和优秀案例 1 的布局层级，不复制品牌、图标、资源或源码。
- 宏页：左侧宽白色“序号 / Python 宏”列表；无效宏仅脚本名红字。右侧窄栏自上而下为名称只读框、启用/停用、编辑、保存、重新加载、删除。只有启用/停用可用；其他按钮是禁用占位。
- 触发页：左侧“宏、按键、模式与次数、状态”四列；右侧 F9、模式、次数、速度为只读配置。功能和设置页仅作低密度对齐与留白调整。
- 未改变 Python 宏接口、自动检测、唯一活动宏、F9/F12、F2 UI 占位、OSD、fail-closed、真实输入路径；没有实现编辑、保存、删除、重载、JSON/QIM、录制、窗口、鼠标、多宏或导入导出。

## 本次一次性取证

- GoalAlignmentMonitor：`DRIFT`，旧文件仍锁定旧七列表格和重复员工流程；纠正后已归档。
- RequirementCertifier：`READY（受限）`，只允许本轮 UI、测试、教程、规则和交接改动。
- CodeExplorer、KnowledgeExpert、UIReferenceAnalyst 均已各完成一次只读取证；后续同一负责人不得自动重复调用 GoalAlignmentMonitor、RequirementCertifier、CodeExplorer、KnowledgeExpert、AntiHallucination。UIReferenceAnalyst 仅在 UI/视觉工作时使用，且先看根目录四图。
- 三个被取消角色文件及其工作区文档、快照引用已经移除。保留 DocUpdater、Handover、TestEngineer。默认不提交、不推送。

## 自动验证与未覆盖风险

在 `my-automation-tool` 执行：

- `python -m unittest discover -s tests -v`：29/29 通过。
- `python -m compileall -q main.py src macros`：通过。
- `git diff --check`：通过。

已逐页生成并查看离屏截图；布局与粉红主题符合本轮目标。离屏环境缺中文字体，且不会发送真实输入，因此 Windows 字体/缩放与记事本 F9/F12 行为必须由用户按教程确认。
