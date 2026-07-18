# 项目大纲

## 当前唯一任务（2026-07-18）

用户已确认 Stage 3K 原教程第 2–6 步通过；第 1 步“键位表可见”失败已修复。当前 Stage 3K 反馈增量已自动验证：设置页整体纵向滚动、删除确认后移入回收站、已启用宏可编辑保存改名且下次 F9 生效；F9/F12/F2、唯一活动宏、停止释放和 fail-closed 保持。当前唯一用户动作是按 `my-automation-tool/docs/test-plans/STAGE_3K_FEEDBACK_DELETE_ACTIVE_EDIT_MANUAL_TEST.md` 做 Windows 验收。多宏并行、Stage 3M、Stage 4T、独立代码清理和发布均未实现、未提交、未推送。

---

## 交接摘要 / 当前状态

### 当前版本
v021.1 / V023（2026-07-16，外观、安全与中文显示均获用户验收；本次明确不提交、不推送）

### 团队模型
项目负责人和全部专项员工永久统一为 `GPT-5.6 Terra 高 / high`；项目文件不得改成其他模型或档位。实际运行分配由 Codex 平台控制，发现不一致时必须如实报告。

### 上一个 AI 做了什么（审查 #13，2026-07-15）
- 根据用户真实测试与 Quickinput `down` 模式，修复 F9 长按重复触发
- F9 改为按住循环、松开/F12 停止，并补齐绿色开始与红色停止 OSD
- 为输入模拟增加可取消机制；自动化验证边沿去重、停止、线程和锁释放
- 审查并标记旧版重复交接/测试文档，创建 v013 快照

### 最新用户实测（审查 #13）
- 修复前按住 F9 会重复打印 Hello World，且没有停止提示；日志已确认。
- 修复后用户已确认：F12 红绿切换、F9 按住循环、松开红色停止提示、停止后无继续输出，全部通过。

### 下一个 AI 要做什么
本段是旧历史摘要；当前唯一任务以文件顶部为准。Stage 2C-T 已获 READY 并实施，自动检查完成后只等待用户按 `my-automation-tool/docs/test-plans/STAGE_2C_EDITABLE_PROMPT_MANUAL_TEST.md` 进行 Windows 验收。Stage 2D 触发页、Stage 3K 全局游戏键位、Stage 3M 鼠标 API 与 Stage 4T 系统托盘均未实现、未提交、未推送。

### 用户需要做什么
用户已确认 V022 视觉规格。本轮无需重复运行 F9/F12/F2；真正 UI 改动后才重新执行 Windows 外观和记事本安全验收。

---

 键盘自动化序列播放器

> 最后维护：2026-07-15 | 当前阶段：文档拆分+环境配置+阶段重构 | 操作者：Codex

---

## 当前进度

| 阶段 | 进度 | 说明 |
|------|------|------|
| 阶段0：环境初始化 | 100% | 骨架目录、文档、日志、配置 |
| 阶段0.5：学习优秀案例 | 100% | 已提取 Quickinput + ok-ww 设计模式 |
| 阶段1.0：安全机制 | 100% | 启动即禁用 + 全局启用键 + 退出双重清理 |
| 阶段1：Hello World 验证 | 100% | 用户已验收 F12 与 F9 DOWN 模式 |
| 屏幕提示文本功能 | 核心验收 100% | 用户已验收开始/停止提示；配置开关等边界项后续补测 |
| 音效功能 | 候选，未承诺 | 仅可参考 Quickinput；需用户明确决定与独立 READY 后才可进入路线图 |
| 阶段2：最小 JSON 序列播放器 | 历史验收通过，已退出运行路径 | 仅保留为 Python 引擎的验证基础 |
| S2：单 Python 宏运行时 | 实现、自动测试与用户验收 100% | 可信 Python 宏、tap/sleep、固定 F9/F12、热重载 |
| v021：四页 UI 外壳 | 运行/安全验收通过，视觉部分认可 | Candy 粉红四页、F9/F12/OSD 不回归、F2 占位 |
| V022：视觉与窗口规则对齐审查 | 用户确认通过，审查完成 | 以优秀案例 1 和四张参考图锁定美化规格 |
| V023：四页 UI 视觉对齐实现 | 用户验收通过；本次不发布 | 仅布局、文案和 Candy 样式；运行边界不变 |
| C1：Python 宏库管理 | 实现与 Windows 人工验收通过 | 唯一启用状态、自动检测与 fail-closed；后续编辑体验独立演进 |
| Stage 1：粉红双栏宏库与触发总览 | 自动检查与 Windows 人工验收通过 | 左脚本列表/右纵向栏，无效红字；触发四列/右只读栏；不发布 |
| E+：高级扩展 | 候选，未承诺 | 多脚本、可配热键、鼠标、窗口、录制、音效、定时均须独立决定 |

---

## 核心文件索引

| 文件 | 位置 | 用途 |
|------|------|------|
| 项目信心需求文档.md | 根目录 | 最高指令 |
| PROJECT_OUTLINE.md | 根目录（本文件） | 进度地图 |
| REVIEW_LOG.md | 根目录 | 审查摘要 |
| PROJECT_SPEC.md | my-automation-tool/ | 需求规格书 |
| PROJECT_KNOWLEDGE.md | my-automation-tool/ | 参考案例知识 |
| PROJECT_TASKS.md | my-automation-tool/ | 任务清单 |
| main.py | my-automation-tool/ | 程序入口 |
| docs/当前状态与交接指南.md | my-automation-tool/docs/ | AI 交接指南 |
| docs/防幻觉机制.md | my-automation-tool/docs/ | 防 AI 幻觉规则 |
| docs/STAGE_TEST_PLAN.md | my-automation-tool/docs/ | 各阶段测试方法 |
| docs/需求更新-屏幕提示文本.md | my-automation-tool/docs/ | 屏幕提示需求 |
| docs/需求更新-音效功能参考.md | my-automation-tool/docs/ | 音效参考 |
| docs/USER_TEST_GUIDE.md | my-automation-tool/docs/ | 手动测试教程 |
| docs/LESSONS_LEARNED.md | my-automation-tool/docs/ | 经验教训 |
| 项目管理/LATEST.txt | 项目管理/ | 指向最新版本 |

---

**每次 AI 对话前必须阅读本文件 + 项目管理/LATEST.txt 指向的版本文件夹。**

阶段编号、真实状态和“案例能力是否纳入”的唯一对齐结论见 `my-automation-tool/docs/requirements/ROADMAP_ALIGNMENT_AUDIT.md` 与根目录 `STAGE_TEST_PLAN.md`。

### 本轮归档与发布状态

治理、路线图、V022 规格和角色配置已在本地提交 `1c3b141`；V022 用户确认与 V023 实施交接已在本地提交 `51ad74a`。本次接手的远端读取因连接重置而未完成，因此不得仅凭历史文字声称 `51ad74a` 已在 GitHub；网络恢复后必须按 GitHub SOP 重新预检并核验远端 SHA。V023 已由用户验收，但用户明确本次不创建提交、不发布；C1 自动检测与唯一活动状态实现完成且待 Windows 人工验收，未获用户通过不得提交或发布。


---

## GitHub
- https://github.com/ssc8537/AutoClicker
- 已确认发布基线：`bc06485`（v021.1）。本地当前提交为 `51ad74a`；其远端 `master`、功能分支和默认 HEAD 状态须在网络可用时重新核验，禁止猜测或强推。

## 根目录文件
- PROJECT_OUTLINE.md
- REVIEW_LOG.md
- 项目信心需求文档.md
- STAGE_TEST_PLAN.md
- .gitignore

---

## 十二、文件拆分防幻觉策略

### 12.1 为什么需要拆分文件
项目文档和测试文件如果写得太长，AI 在阅读时容易产生幻觉（遗漏内容、混淆信息）。把大文件拆成小文件，每个文件只包含少量内容，AI 能更准确地理解和执行。

### 12.2 拆分原则
1. **每个文件不超过 100 行或 3 个阶段内容**
2. **测试计划拆分到 docs/test-plans/ 目录**，按阶段分组：
   - STAGE_1-2.md：阶段1 + 阶段1.5 + 阶段2
   - STAGE_3-4.md：阶段3 + 阶段4
   - STAGE_5+.md：阶段5 + 未来阶段（可追加）
3. **所有测试文件通过根目录的 STAGE_TEST_PLAN.md（总索引）引用**
4. **新增阶段时不修改旧文件**，追加到 STAGE_5+.md 末尾或新建文件

### 12.3 接手 AI 如何阅读
1. 先读 STAGE_TEST_PLAN.md（总索引），了解整体结构
2. 根据当前阶段打开对应的测试文件
3. 如果当前阶段是进行中的，看该阶段的测试清单
4. 如果当前阶段还没实现，看需求说明即可
5. 新阶段追加到 STAGE_5+.md 的末来阶段后面

### 12.4 文件索引更新规范
- 新增阶段文件后，必须更新 STAGE_TEST_PLAN.md 总索引的表格
- 修改文件路径或文件名后，必须更新所有引用该文件的文档
- 定期检查 docs/test-plans/ 目录下的文件，确保索引与实际文件一致
