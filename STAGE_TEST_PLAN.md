# 阶段测试计划 - 总索引

## Stage 3K：反馈修复、删除与启用宏编辑（自动检查完成，待 Windows 人验）

- 范围：修复八项键位表可滚动可见；确认后回收站删除；已启用宏可编辑、保存和改名，但当前运行快照不变、下次 F9 生效。
- 禁止：鼠标、额外热键、角色/动画/CD 检测、多宏并行、系统托盘、发布及未获独立 READY 的代码清理。
- 自动验证：键位表可见、确认取消、回收站成功/失败、活动宏删除停止/清空/F9 fail-closed、活动宏保存改名路径同步，以及既有配置、F9/F12/F2、宏扫描、唯一启停、触发表回归；全量单元测试 52/52、编译和差异检查通过。
- 人工验收：按 `my-automation-tool/docs/test-plans/STAGE_3K_FEEDBACK_DELETE_ACTIVE_EDIT_MANUAL_TEST.md` 在记事本完成；不运行游戏输入。

## Stage 2D：触发页表格视觉修订（Windows 人验通过）

- 范围：触发页表格新增“序号”列；名称显示去 `.py`；所有表头和单元格居中。
- 禁止：不修改唯一启用/停用、无效红字、右侧只读详情、F9/F12/F2、OSD、fail-closed、宏执行或真实输入。
- 自动验证：五列表头、从 1 连续的序号、名称无 `.py`、表头/单元格居中、状态列唯一启停、无效红字、右侧详情与横向滚动/F9/F12/F2 回归均由离屏测试覆盖；全量单元测试 41/41、编译和差异检查通过。
- 人工验收：用户已按 `my-automation-tool/docs/test-plans/STAGE_2D_TRIGGER_TABLE_VISUAL_MANUAL_TEST.md` 确认通过；不运行游戏输入。

## Stage 2C-U：切人时序作者规则修订（Windows 人验通过）

- 范围：仅同步 `ai_prompt.txt`、`ai_prompt.default.txt`、作者手册、自动测试和独立中文 Windows 教程；普通切人统一 50ms，回切统一 1080ms，R 后统一 1500ms。
- 禁止：不修改热键、真实输入、宏执行、UI 行为、动画/CD/当前角色检测或角色语义 API。
- 自动验证：出厂双模板一致、六方向、50ms/1080ms/1500ms、R 示例无额外等待；全量单元测试 41/41、编译和差异检查通过。文件恢复、UTF-8 失败不覆盖、源码只读附带、F9/F12 回归继续由既有测试覆盖。
- 人工验收：用户已按 `my-automation-tool/docs/test-plans/STAGE_2C_U_SWITCH_TIMING_REVISION_MANUAL_TEST.md` 完成 1–4 步并确认通过；不运行游戏输入。

## Stage 2C-T：可编辑提示词文件与大招切人规则（Windows 人验通过）

- 已实现：项目 `config/ai_prompt.txt` 可由用户直接编辑，`config/ai_prompt.default.txt` 是不可自动改写的默认备份；提示词窗口每次打开重新读取当前文件，显示绝对路径与恢复说明，并在缺失/UTF-8 失败时安全回退。
- 自动验证：首次恢复、外部编辑后重开、路径显示、复制、缺失恢复、乱码不覆盖、双文件不可读、默认备份不被改写、源码只读附带，以及 R 后 1800ms 示例均有覆盖；F9/F12 不修改。
- 人工验收：用户已按 `my-automation-tool/docs/test-plans/STAGE_2C_EDITABLE_PROMPT_MANUAL_TEST.md` 完成 1–6 步并确认通过；不运行游戏输入。

## Stage 2C-S：三角色切人规则（Windows 人验通过）

- 已实现：角色名称填写区、六方向普通切人 60ms、任意回切 1100ms、数字键不变的注释要求和作者手册。
- 人工验收：用户已按 `my-automation-tool/docs/test-plans/STAGE_2C_SWITCH_TIMING_MANUAL_TEST.md` 完成 1–4 步并确认通过；该阶段不运行真实游戏输入。

## Stage 2C-R：纯文本提示词与作者说明（Windows 人验通过）

- 已实现：纯文本提示词、函数和元数据解释、Q 声骸技能/R 大招参考、完整作者手册，以及原样源码注释保留。
- 人工验收：仅按 `my-automation-tool/docs/test-plans/STAGE_2C_AI_PROMPT_MANUAL_TEST.md` 验收本轮反馈修复。

## Stage 2C：AI 提示词复制（Windows 人验通过）

- 已实现：宏页“编辑”下方的始终可用按钮、只读中文提示词窗口、剪贴板复制、有效宏的已保存源码附带与安全回退。
- 自动验证：按钮位置、只读性、复制反馈、有效/无效/未选中/读取失败回退，以及既有 F9/F12 回归均已覆盖；完整测试 40/40 通过。
- 人工验收：仅按 `my-automation-tool/docs/test-plans/STAGE_2C_AI_PROMPT_MANUAL_TEST.md` 验收复制与显示。Stage 2D、3K、3M、4T 不在本轮。

## Stage 1：宏库信息总览（Windows/记事本人验通过）

自动检查必须验证：Candy 粉红宏页是左侧脚本列表和右侧纵向禁用操作栏；宏页选择不得改变活动宏，无“校验”或“错误摘要”，无效宏仅脚本名红字。触发页必须列出全部发现脚本，固定“名称、按键、模式、状态”四列；仅有效行的状态列可切换唯一活动宏，无效行不可启用，右侧栏只读。现有自动检测、F9/F12、F2 占位、OSD 与 fail-closed 行为没有回归。

人工验收必须使用独立中文小白教程，只要求用户观察宏库 UI 和在记事本验证既有 F12/F9 安全行为。教程须包含启动命令、准备条件、逐步操作、每步预期、失败反馈模板及未覆盖风险。不得要求用户理解代码、内部状态或自动测试术语。

## Stage 2A：可信 Python 宏文件管理（Windows 人验通过）

自动检查必须验证：新建模板只做静态扫描、不执行顶层代码；名称、文件名和 `NAME` 元数据同步；非法/冲突名称及活动宏重命名被拒绝；语法或接口错误、写入失败都不会覆盖旧文件；重新加载同步宏页和触发页列表。既有 F9/F12/F2、OSD、唯一活动宏和 fail-closed 不得回归。

人工验收使用 `STAGE_2A_PYTHON_MACRO_MANAGEMENT_MANUAL_TEST.md`：新建、编辑、保存、重命名、错误保存回退、活动宏保护和 F9/F12 回归。导入导出、删除、快捷键配置、多宏、鼠标和录制均不属于本阶段。

## Stage 2B：Python 编辑体验（Windows 人验与 Enter 反馈修复均已通过）

宏列表只显示 Python 文件主体且无效项保持红字；单击仅选中，右侧名称框 Enter 与“保存”共用原子重命名。新建/编辑窗口必须显示中文“保存/取消”，代码区提供 Python 彩色高亮和四空格 Tab 缩进。不得改变 Stage 2A 文件服务、F9/F12/F2、OSD、唯一活动宏或真实输入路径。

人工验收使用 `STAGE_2B_EDITOR_EXPERIENCE_MANUAL_TEST.md`。游戏键位配置、键盘语义 API、鼠标 API、删除与导入导出均不属于本阶段。

> 最后更新：2026-07-16 | 操作者：项目负责人
>
> 本文件是测试计划的索引页。具体测试内容已按阶段拆分到多个文件。
> 每个文件包含 2-3 个阶段，方便阅读和更新。

---

## 核心思想

Hello World 是键盘输入、停止与安全边界的最小验证信号；它不能单独证明 UI、配置或未来候选功能已经完成。

阶段完成必须同时满足：当前产品决定、自动验证、Windows 人工验收（涉及真实输入时）和对应需求门槛。优秀案例只提供结构与安全思路，不自动扩大本项目承诺。

---

## 测试文件索引

| 文件 | 包含阶段 | 状态 |
|------|---------|:----:|
| my-automation-tool/docs/test-plans/STAGE_1-2.md | 已验收安全/OSD、历史 JSON 基线、已验收单 Python 宏 | 已更新 |
| my-automation-tool/docs/test-plans/STAGE_3-4.md | v021/V022 UI 与下一核心候选 | 已更新 |
| my-automation-tool/docs/test-plans/STAGE_1_MACRO_OVERVIEW_MANUAL_TEST.md | Stage 1 宏库信息总览的 Windows/记事本验收 | 待用户执行 |
| my-automation-tool/docs/test-plans/STAGE_2A_PYTHON_MACRO_MANAGEMENT_MANUAL_TEST.md | Stage 2A Python 宏文件管理的 Windows 验收 | 用户通过 |
| my-automation-tool/docs/test-plans/STAGE_2B_EDITOR_EXPERIENCE_MANUAL_TEST.md | Stage 2B Python 编辑体验的 Windows 验收 | 待用户执行 |
| my-automation-tool/docs/test-plans/STAGE_5+.md | 候选扩展（不构成当前交付承诺） | 已更新 |
| my-automation-tool/docs/requirements/ROADMAP_ALIGNMENT_AUDIT.md | 阶段—案例—产品决定的追溯结论 | 新增 |

---

## 测试进度总览

| 阶段 | 内容 | 测试状态 |
|------|------|:--------:|
| S1 | 安全 Hello World | 用户验收通过 |
| S1.5 | OSD 核心提示 | 用户声明完整通过；旧的三个未勾项目需补齐证据或归档，不能伪造自动验收 |
| H2（历史） | 最小 JSON 播放器 | 历史验证基线，已退出运行路径，不是当前待办 |
| S2 | 单 Python 宏运行时 | 自动与用户验收通过：F9/F12、`switch/down`、COUNT/SPEED、可取消与热重载 |
| v021 | 四页 UI 外壳 | 运行/安全验收通过；视觉仅部分认可 |
| V022 | 视觉与窗口规则对齐 | 用户确认、V023 受限实现和验收均已完成；历史审查门槛不再作为当前阻塞 |
| V023 | 四页 UI 视觉对齐与中文化 | 用户已通过外观、安全和中文显示；本次明确不提交、不推送 |
| C1（候选核心） | Python 宏库管理 | 自动检测与唯一活动状态实现完成：29/29 自动验证通过，Windows/真实输入人工验收待完成；未承诺编辑或保存行为 |
| Stage 1 | 优秀案例 1 风格的宏库信息总览 | 用户 Windows/记事本验收通过 |
| Stage 2A | Python 宏新建、重命名、编辑、原子保存、重新加载 | 37/37 自动验证与 Windows 人工验收通过；不发布 |
| Stage 2B | 无后缀列表、Enter 改名、中文 Python 编辑器 | 原始 Windows 验收与 Enter 缩进反馈均已通过，不发布 |
| E+（候选扩展） | 多脚本、可配热键、鼠标、窗口、录制、音效、定时 | 不属于当前承诺；每项需用户决定与独立 READY |

---

## 如何使用这些测试文件

1. **接手 AI**：先读总索引，再按阶段打开对应的测试文件
2. **用户**：按当前阶段的测试清单逐项操作，把 [ ] 改成 [x]
3. **新增阶段**：追加到 STAGE_5+.md 末尾，或在 test-plans/ 目录下新建文件
4. **调整阶段**：修改对应测试文件中的内容，更新总索引表
