# 项目大纲

---

## 交接摘要 / 当前状态

### 当前版本
v017（2026-07-16，阶段 2 JSON 按 F9 热重载，待用户验收）

### 上一个 AI 做了什么（审查 #13，2026-07-15）
- 根据用户真实测试与 Quickinput `down` 模式，修复 F9 长按重复触发
- F9 改为按住循环、松开/F12 停止，并补齐绿色开始与红色停止 OSD
- 为输入模拟增加可取消机制；自动化验证边沿去重、停止、线程和锁释放
- 审查并标记旧版重复交接/测试文档，创建 v013 快照

### 最新用户实测（审查 #13）
- 修复前按住 F9 会重复打印 Hello World，且没有停止提示；日志已确认。
- 修复后用户已确认：F12 红绿切换、F9 按住循环、松开红色停止提示、停止后无继续输出，全部通过。

### 下一个 AI 要做什么
阶段 2 的三项实现及自动测试已完成，随后按 Quickinput 修正为 switch/down 两种模式、F12 全局 OSD 和 F9 前 JSON 热重载。现在由用户按 `my-automation-tool/docs/USER_TEST_GUIDE.md` 验收：保存 `count: 1` 后轻按 F9 完整输出一次；保存 `count: 0` 后按住循环、松开停止，均无需重启。

### 用户需要做什么
按 docs/test-plans/STAGE_1-2.md 的阶段1.5测试清单验证 OSD 功能

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
| 音效功能 | 0% | 需求已记录，待后续实现（参考 Quickinput 音效） |
| 阶段2：最小 JSON 序列播放器 | 实现与自动测试 100%，待热重载用户验收 | 一个测试宏、可中断播放器、固定 F9/F12、switch/down、次数/速度热重载 |
| 阶段3：热键绑定 UI + 脚本编辑器 | 0% | script_engine.py 待创建 |
| 阶段4：窗口匹配 + 高级功能（音效/定时）| 0% | UP模式、冲突检测 |
| 阶段5：完善与优化（多脚本并发/持久化）| 0% | main_window.py + script_editor.py |
| 阶段6-8 | 0% | 并发、持久化、测试 |

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


---

## GitHub
- https://github.com/ssc8537/AutoClicker
- master+V1

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
