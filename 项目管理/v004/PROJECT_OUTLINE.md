# 项目大纲

---

## 交接摘要 / 当前状态

### 当前版本
v004（2026-07-15）

### 上一个 AI 做了什么（Codex，2026-07-15）
- 用户手动测试阶段1.0（安全机制）全部通过
- 整理了屏幕提示文本需求（参考 Quickinput PopsUi 实现）
- 整理了音效功能参考（Quickinput 5 个音效文件 + 12 种事件绑定）
- 用 Hello World 贯穿法设计了阶段测试计划（阶段2-8）
- 创建防幻觉机制文档（7 条核心规则）
- 创建当前状态与交接指南
- 更新了根目录所有关键文档

### 下一个 AI 要做什么
1. 先读完所有文档（按当前状态与交接指南.md 的阅读顺序）
2. 目前是文档阶段，下一个 AI 可以开始代码实现
3. 优先级：屏幕提示文本功能 > 阶段2序列播放器 > 阶段3脚本引擎

### 用户需要做什么
按 docs/阶段测试计划.md 的阶段测试方法验证每个功能

---

 键盘自动化序列播放器

> 最后维护：2026-07-15 | 当前阶段：文档整理完成 | 操作者：Codex

---

## 当前进度

| 阶段 | 进度 | 说明 |
|------|------|------|
| 阶段0：环境初始化 | 100% | 骨架目录、文档、日志、配置 |
| 阶段0.5：学习优秀案例 | 100% | 已提取 Quickinput + ok-ww 设计模式 |
| 阶段1.0：安全机制 | 100% | 启动即禁用 + 全局启用键 + 退出双重清理 |
| 阶段1：Hello World 验证 | 100% | 用户手动实测通过 |
| 屏幕提示文本功能 | 0% | 需求已记录，待实现（参考 Quickinput Pops） |
| 音效功能 | 0% | 需求已记录，待后续实现（参考 Quickinput 音效） |
| 阶段2：序列播放器 | 0% | sequence_player.py 待创建 |
| 阶段3：脚本引擎 | 0% | script_engine.py 待创建 |
| 阶段4：热键管理完善 | 0% | UP模式、冲突检测 |
| 阶段5：主 UI 界面 | 0% | main_window.py + script_editor.py |
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
| docs/阶段测试计划.md | my-automation-tool/docs/ | 各阶段测试方法 |
| docs/需求更新-屏幕提示文本.md | my-automation-tool/docs/ | 屏幕提示需求 |
| docs/需求更新-音效功能参考.md | my-automation-tool/docs/ | 音效参考 |
| docs/用户验收测试指南.md | my-automation-tool/docs/ | 手动测试教程 |
| docs/LESSONS_LEARNED.md | my-automation-tool/docs/ | 经验教训 |
| 项目管理/LATEST.txt | 项目管理/ | 指向最新版本 |

---

**每次 AI 对话前必须阅读本文件 + 项目管理/LATEST.txt 指向的版本文件夹。**
