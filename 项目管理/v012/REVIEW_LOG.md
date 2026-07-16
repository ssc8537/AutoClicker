# 项目审查日志（REVIEW LOG）

> 当前版本：v012 | 最后更新：2026-07-15 | 操作者：Codex
>
> **完整历史审查记录见 `my-automation-tool/docs/reviews/` 目录。** 本文件只保留当前状态、最近审查和可直接交接的信息。

---

## 当前状态摘要

| 项目 | 状态 |
|---|---|
| 阶段 1：Hello World + 安全机制 | 已完成，用户曾手动验证 |
| 阶段 1.5：OSD | 代码完成，仍待用户手动测试（2.7） |
| Qt 热键线程安全 | 审查 #12 已修复，待用户压力验证 |
| 下一开发阶段 | 阶段 2：脚本管理系统 |
| 当前快照 | `项目管理/v012/` |

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

---

## ▼ 给下一个 AI 的提示词（从这里复制）

你正在维护 **MyAutoPlayer**（Python + PySide6 的键盘自动化序列播放器）。当前版本为 **v012**，快照在 `项目管理/v012/`。

### 当前状态

- 阶段 1 和安全机制已完成；F12 为全局启用/禁用键，F9 打出 Hello World。
- 阶段 1.5 OSD 已完成，但 **2.7 手动测试仍待用户**。
- F9/F12 钩子线程已通过 `_HotkeyDispatcher` 转发到 Qt 主线程；连按 F9 使用非阻塞锁丢弃，不可改回直接访问 Qt UI。
- 下一功能阶段为阶段 2：脚本管理系统；不要在用户完成 OSD 手动测试前声称阶段 1.5 已验收。

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
