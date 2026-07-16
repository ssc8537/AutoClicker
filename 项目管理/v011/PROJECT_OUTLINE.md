# 项目大纲

---

## 交接摘要 / 当前状态

### 当前版本
v011（2026-07-15，快照目录待创建）

### 上一个 AI 做了什么（过去本，2026-07-15）
- 修复了 审查 #7 的全部乱码（54行原文不可逆损坏，根据上下文完整重构）
- 为 SETUP_GUIDE.md 添加 UTF-8 BOM，防止 PowerShell 误渲染
- 更新 PROJECT_TASKS.md / PROJECT_OUTLINE.md / REVIEW_LOG.md 同步进度

### 下一个 AI 要做什么
详见 REVIEW_LOG.md 末尾的「给下一个 AI 的提示词」。
优先级：
1. 文档规则更新（规则6-1 + 防止问题复发）
2. REVIEW_LOG.md 拆分（按 docs/reviews/ 目录归档）
3. 漏洞修复（main.py 的 _HotkeyDispatcher + osd_window.py）

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
| 阶段1：Hello World 验证 | 100% | 用户手动实测通过 |
| 屏幕提示文本功能 | 90%（代码完成+乱码修复，待用户测试） | OSD浮层窗口创建、配置项、main.py集成已完成，等待用户手动测试 |
| 音效功能 | 0% | 需求已记录，待后续实现（参考 Quickinput 音效） |
| 阶段2：脚本管理系统（热键绑定+触发模式+执行次数） | 0% | sequence_player.py 待创建 |
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
