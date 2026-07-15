# 项目大纲 ---

## 交接摘要 / 当前状态

### 当前版本
v003（2026-07-15）

### 上一个 AI 做了什么（Codex，2026-07-15）
- 完成了阶段1.0 安全机制（6 个子任务全部落地）
- hotkey_manager.py 启动即禁用 + F12 全局切换 + 退出双重清理
- 自动化端到端测试通过
- 编写了用户验收测试指南（含新手上路教程）
- 重写了项目信心需求文档.md（角色定位 + 工作流程 + 交接协议）

### 下一个 AI 要做什么
1. 等用户手动验收阶段1.0 通过后
2. 创建 src/core/sequence_player.py（序列播放器 - 阶段2）
3. 参考 PROJECT_SPEC.md 的 sequence_player 接口设计
4. 编写自动化测试验证
5. 创建 v004 快照

### 用户需要做什么
按 docs/用户验收测试指南.md 的新手上路章节启动程序，逐项测试 7 步。

---

 键盘自动化序列播放器

> 最后维护：2026-07-15 | 当前阶段：阶段1.0（安全机制 --- 已完成）| 操作者：Codex
>
> **阶段1.0（安全机制）已于 2026-07-15 完成。自动化端到端实测通过：**
> - 启动即禁用（_global_disabled = True）
> - F12 切换启用/禁用（回调通知 UI 标签）
> - 退出双重清理（closeEvent unhook_all + atexit 兜底）
> - 自动测试验证：禁用时 F9 不触发 / 启用后 F9 打出 Hello World / 再禁用后 F9 不触发
>
> **完整版本历史**：见 项目管理/v001/ 和 项目管理/v002/。项目管理/LATEST.txt 指向最新稳定版本。

本文档是项目的结构地图和进度总览。每次 AI 对话开始前必须阅读。

---

## 当前进度

| 阶段 | 进度 | 说明 |
|------|------|------|
| 阶段0：环境初始化 | 100% | 骨架目录、文档、日志、配置 |
| 阶段1.0：安全机制 | 100% | 启动即禁用 + 全局启用键 + 退出双重清理 + 实测通过 |
| 阶段1：Hello World 验证 | 100% | 自动测试验证：F12 启用后 F9 打出 Hello World |
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
| docs/用户验收测试指南.md | my-automation-tool/docs/ | 手动测试指南（每阶段需你检查的内容） |
| LESSONS_LEARNED.md | my-automation-tool/docs/ | 经验教训：孤儿进程 + 残留钩子 |
| 项目管理/LATEST.txt | 根目录 | 指向最新稳定版本 |

---

**每次 AI 对话前必须阅读本文件 + 项目管理/LATEST.txt 指向的版本文件夹。**
