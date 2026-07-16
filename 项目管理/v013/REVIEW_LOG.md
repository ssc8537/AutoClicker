# 项目审查日志（REVIEW LOG）

> 当前版本：v013 | 最后更新：2026-07-15 | 操作者：Codex
>
> **完整历史审查记录见 `my-automation-tool/docs/reviews/` 目录。** 本文件只保留当前状态、最近审查和可直接交接的信息。

---

## 当前状态摘要

| 项目 | 状态 |
|---|---|
| 阶段 1：Hello World + 安全机制 | 用户已重新手动验收通过 |
| 阶段 1.5：OSD | 核心开始/停止提示已由用户验收通过 |
| Qt 热键线程安全 | 自动化与用户真实键盘测试均通过 |
| 下一开发阶段 | 阶段 2 前的真实需求对齐审查 |
| 当前快照 | `项目管理/v013/` |

## 审查 #10 | 2026-07-15 | 操作者：Codex

修复 PySide6 6.11.1 的启动崩溃：`QGraphicsDropShadowEffect` 应从 `PySide6.QtWidgets` 导入，而不是 `QtGui`。程序需以 `python main.py` 复核完整错误；旧 `__pycache__` 可能保留旧导入。

## 审查 #11 | 2026-07-15 | 操作者：Codex

历史审查 #7 曾出现不可逆乱码，已根据代码、任务清单和其他审查记录还原。`SETUP_GUIDE.md` 原本宣称已加 UTF-8 BOM，但本轮检查发现实际未带 BOM；该不一致已在审查 #12 修正并记录。

## 审查 #12 | 2026-07-15 | 操作者：Codex

### 发现的问题与修复

1. `keyboard` 的全局热键回调在后台钩子线程运行，却直接调用输入、OSD 和 Qt 标签，存在跨线程 UI 访问风险。
2. 快速连按 F9 可使执行重叠，缺少丢弃策略。
3. `SETUP_GUIDE.md` 实际没有 UTF-8 BOM，和交接记录不一致。

`main.py` 新增 `_HotkeyDispatcher(QObject)`：钩子线程只发射 `f9_signal` / `toggle_signal`，Qt 主线程执行输入、OSD 和状态更新。F9 通过非阻塞锁拒绝连按，并在成功、异常及信号转发失败时释放锁。OSD 改为无父窗口全局浮层。规则、经验教训、任务清单与大纲均已同步；历史审查 #5-#9 已归档。

### 验证与剩余事项

- 已完成：源码编译、BOM 首字节、日志归档和 v012 快照结构核对。
- 待用户：按 `docs/test-plans/STAGE_1-2.md` 验证 OSD；在记事本外启用 F12 后快速连按 F9，确认不冻结、OSD 正常且没有并发输入。

## 审查 #13 | 2026-07-15 | 操作者：Codex

### 用户实测发现

用户按住 F9 时，记事本持续输出 Hello World；`logs/app.log` 在 23:12:33–23:13:06 记录了连续多次 “F9 触发”。成功 OSD 能显示，但松开 F9 没有停止 OSD。

### 修复结果

经需求文档和用户实测确认，F9 采用“按住连续执行、松开停止并提示”。已参考 Quickinput 的 `down` 分支完成：

`hotkey_manager.py` 改用按下/释放边沿，取代会重复触发的 `add_hotkey`；F12 长按只切换一次，并会停止 DOWN 脚本。`type_string` 支持 `stop_event`；`main.py` 使用可取消后台循环，Qt 主线程只更新开始/停止 OSD。自动化回归已验证边沿去重、F12 停止、输入取消、主线程 OSD 与执行锁释放。

### 用户最终手动验收（2026-07-15）

用户已确认以下结果全部通过：

1. F12 能正确在红色“禁用”和绿色“启用”间切换。
2. 按住 F9 时持续循环输入 Hello World。
3. 松开 F9 时显示红色停止弹窗，且之后不再继续输出。

阶段 1 与阶段 1.5 的核心验收通过，可以进入下一阶段。后续涉及电脑界面的测试一律由用户操作；AI 只运行程序或命令、读取日志并分析结果。

### 文档审查结论

`OSD_POPUP_REQUIREMENT.md` 已明确规定“脚本结束 / 松开按键”显示红色结束提示，因此用户期望是既有需求漏实现，不是临时新增需求。已将 F9 默认 DOWN 语义写入 `PROJECT_SPEC.md` 和用户测试指南；旧版交接与测试文档已标记为历史归档，避免其 v004/旧阶段信息误导接手 AI。结构审查还发现 `PROJECT_KNOWLEDGE.md`、`USER_TEST_GUIDE.md` 等旧文档超过 100 行；在本轮手动验收后，应单独做文档拆分整理，不能与阶段 2 功能混做。

---

## ▼ 给下一个 AI 的提示词（从这里复制）

你正在维护 **MyAutoPlayer**（Python + PySide6 的键盘自动化序列播放器）。当前版本为 **v013**，快照在 `项目管理/v013/`。

### 当前状态

- F12 为全局启用/禁用键；F9 已固定为 DOWN 模式：按住循环输出 Hello World，松开或 F12 禁用时停止。用户已完成真实键盘验收。
- 热键使用 `keyboard.hook_key` 的按下/释放边沿；不可改回 `add_hotkey`，否则会复发长按重复启动问题。
- 输入循环仅在后台执行 SendInput；OSD 和 Qt 标签只在 `_HotkeyDispatcher` 的 Qt 主线程槽中更新。
- 阶段 1/1.5 自动化和用户真实键盘验收均已通过；允许进入阶段 2，但必须先完成真实需求对齐审查。

### 下一位 AI 的唯一任务顺序

1. **先做需求对齐审查，不写代码。** 逐一比对 `PROJECT_SPEC.md`、`PROJECT_KNOWLEDGE.md`、`PROJECT_TASKS.md`、当前代码和 Quickinput 的 `trigger.cpp`；输出“当前实现/用户已验收行为/真实游戏目标/文档冲突”四列表。旧版 `HANDOVER_GUIDE.md` 与 `docs/STAGE_TEST_PLAN.md` 已标为历史，不可作为需求来源。
2. **确定阶段 2 的最小边界并写入文档。** 阶段 2 只交付一个可加载的 JSON Hello World 宏、可中断的 `SequencePlayer`、脚本的热键/模式/次数/速度配置；不做主 UI、脚本编辑器、窗口匹配、音效或多脚本并发。
3. **需求完全对齐后再分三项实现。** 先实现并自动测试可取消 `SequencePlayer`；再实现 JSON 宏加载与校验；最后将一个测试宏接入当前热键管理器。每项完成后更新日志，所有界面测试交给用户。

### 接手必读顺序

1. `项目信心需求文档.md`
2. `my-automation-tool/docs/rules/01-角色与工作流程.md` 至 `04-项目策略与规范.md`
3. `PROJECT_OUTLINE.md`、本文件、`my-automation-tool/PROJECT_TASKS.md`
4. `my-automation-tool/docs/LESSONS_LEARNED.md`、`my-automation-tool/docs/ANTI_HALLUCINATION.md`
5. `STAGE_TEST_PLAN.md` 与 `my-automation-tool/docs/test-plans/STAGE_1-2.md`

### 强制规则

- 先在 Quickinput 与 ok-ww 两个优秀案例源码中找答案；都找不到时删除该小功能并从头重写，不要在坏代码上修补。
- 发现任何 bug、设计缺陷、编码错误或策略失误，必须同步记录 `REVIEW_LOG.md` 与 `docs/LESSONS_LEARNED.md`，禁止沉默修复。
- 中文文件只用 `apply_patch` 改动；一次最多做三个子任务；结束时更新项目快照。
- `SETUP_GUIDE.md` 必须保留 UTF-8 BOM；程序日志在 `my-automation-tool/logs/app.log`。
