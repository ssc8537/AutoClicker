# 项目审查日志（REVIEW LOG）

> 当前版本：v014 | 最后更新：2026-07-15 | 操作者：Codex
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
| 当前快照 | `项目管理/v014/` |

## 审查 #15 | 2026-07-16 | 操作者：Codex

用户完成阶段 2 的最终范围确认：唯一宏固定 F9，F12 固定全局启停；宏用 SendInput 逐键输出小写 `hello world`，不用 Unicode `text`。模式只有 `switch`、`down`、`up`，`count` 为 `0–99`（0 为无限），`speed` 为 `0.01–8.0`，仅缩放释放后的动作间隔。

审查发现 v014 的最小规格仍保留早期的 `text` 步骤、JSON 热键、`0–9999` 次和 `0.1–10×` 范围；这些均已按用户最新确认修正。经验教训已同步至 `docs/LESSONS_LEARNED.md`。阶段 2 仍不含 UI、鼠标、窗口匹配、音效、Python 脚本、组合键、热键自定义或多宏并发。

## 审查 #16 | 2026-07-16 | 操作者：Codex

阶段 2 三项实现完成：新增单实例、可中断 `SequencePlayer`；新增严格 JSON 加载器和 `config/hello_world_macro.json`；主程序改为固定 F9/F12 接入 JSON 宏。播放器在按键保持或步骤等待中收到停止请求时都会结束，并释放当前按键；同一实例重复启动被拒绝。有限次数自然结束时，热键管理器状态也会复位。

已运行 `python -m unittest discover -s tests -v`：12 项通过，覆盖 JSON 合法/非法输入、次数/速度边界、顺序执行、速度换算、中断释放、重复启动拒绝和三种模式状态机。已运行语法编译及实际宏加载检查；未启动 GUI，未发送真实键盘输入。用户手动验收改按 `docs/USER_TEST_GUIDE.md` 的阶段 2 步骤执行。

## 审查 #17 | 2026-07-16 | 操作者：Codex

用户已确认阶段 2 的物理键盘输入、F12、F9 和停止行为的原始测试成功。随后发现窗口说明错误显示字面量 `\\n`，并要求 F12 也使用 OSD 提示。已修正为真实换行；F12 启用显示绿色“全局脚本已就绪”，禁用显示红色“全局脚本已禁用”。

经再次核对 Quickinput `trigger.cpp`：`down` 的释放停止只适用于 `count == 0`。本项目据此删除 `UP` 和 `PRESS`，仅保留 `switch` 与 `down`；默认宏改为 `down + count: 1`，轻按 F9 会完整输出一次 `hello world`，设置 `count: 0` 才恢复按住循环、松开停止。16 项自动测试通过；本次变更仍需用户按更新后的教程验收。

## 审查 #18 | 2026-07-16 | 操作者：Codex

用户确认阶段 2 的窗口文字、F12 全局 OSD、轻按一次完整输出、`count=0` 按住循环和鼠标窗口抑制均测试通过。剩余问题是：编辑器保存 JSON 后仍需重启才会生效。

已参考 Quickinput 的内存配置提交模型，新增按 F9 启动前的 JSON 严格重载：下一次 F9 使用新保存的 `count`、`mode`、`speed` 和步骤，无须重启；正在播放的序列不变。无效 JSON 会阻止启动、保留最后有效配置并显示错误 OSD。18 项自动测试通过；待用户按教程验证保存 `count: 1` 与 `count: 0` 后均可立刻生效。

## 审查 #19 | 2026-07-16 | 操作者：Codex

用户确认阶段 2 的全部手动测试通过，并更新产品方向：脚本只用可信本地 Python，不再使用 JSON。阶段 3 已新增 `scripts/hello_world.py`、Python 宏加载/热重载、`ScriptPlayer.tap/sleep` 和通用 `SequencePlayer`；Quickinput 的热键框架和优秀案例 2 的小输入接口均被保留，图像识别与状态判断未引入。

实现中发现标准 Python 导入缓存会让快速保存、长度相同的脚本继续使用旧内容；已改为每次 F9 直接读取、编译和执行源码。语法/元数据错误将拒绝启动并显示红色 OSD，最后有效宏保留。16 项自动测试、语法检查均通过；待用户按 Python 教程验收。

## 审查 #14 | 2026-07-15 | 操作者：Codex

### 真实需求对齐结论（未写代码）

| 当前实现 | 用户已验收行为 | 真实游戏目标 | 文档冲突与处理 |
|---|---|---|---|
| F12 默认禁用、F9 `DOWN`、鼠标在程序窗口内抑制、关闭时清理热键 | F12 红绿切换；按住 F9 输出 Hello World；松开即停止并显示红色提示 | 仅在用户明确启用后向当前目标窗口发送固定序列，且可随时停止 | 无冲突；阶段 2 必须保留这些安全行为。 |
| `HotkeyManager` 已有 `switch`、`down`、`up` 和按下边沿去重 | 只验收过 F9 `DOWN` | 游戏宏需要按配置选择触发模式 | 阶段 2 只复用前三种模式；旧的 `PRESS`、组合键和冲突检测不纳入。 |
| `type_string` 可在字符间取消；没有 `SequencePlayer`、宏加载或宏接入 | 用户未验收 JSON 宏 | 固定序列要按顺序、按次数和速度执行，并能停止 | 先实现可中断播放器；不把阶段 1 的 Hello World 循环继续塞入 `main.py`。 |
| `input_simulator` 已有键盘/鼠标底层能力 | 只验收文本输出 | 最终游戏目标是角色切换与技能的固定序列，延迟目标约 10ms | 阶段 2 测试宏只允许 `text` 步骤；游戏按键/鼠标和 10ms 精度留给后续需求。 |
| 无 UI、无脚本编辑器、无窗口匹配、无并发 | 用户已能按教程测试 | 未来可视化管理与高级功能 | 旧规格中的 Python 脚本、UI、多宏并发、窗口匹配、音效及辅助组合键均明确排除。 |

### 已锁定的阶段 2 最小范围

唯一规格文件为 `my-automation-tool/docs/阶段2-最小需求规格.md`：一个严格校验的 JSON Hello World 宏、一个可中断 `SequencePlayer`，以及该宏的单热键、`switch/down/up` 模式、次数和速度配置。速度公式锁定为 `delay_ms / speed`；同一时刻拒绝第二次启动。没有修改 Python 代码，也没有运行界面测试。

### 发现的文档问题

1. 已核验：`项目信心需求文档.md` 的规则索引与实际的 `02-交接协议与日志规范.md`、`03-问题解决与自检规则.md` 一致；先前按臆测文件名阅读是审查方法错误，不能将其记录为项目文档缺陷。
2. 旧阶段 2 测试计划仍把“创建、编辑和管理”“两个宏热键冲突”“组合键”写进阶段 2；这些超出已锁定范围，已在该节明确标为历史草案。

阶段范围冲突已同步记录到 `docs/LESSONS_LEARNED.md`；本轮未修改任何代码。

### 给下一个 AI 的提示词

你正在维护 MyAutoPlayer。阶段 2 的真实需求已完成对齐，当前版本快照为 v014。先读 `项目信心需求文档.md`、`PROJECT_OUTLINE.md`、`REVIEW_LOG.md`、`my-automation-tool/PROJECT_SPEC.md`、`my-automation-tool/PROJECT_TASKS.md` 和 `my-automation-tool/docs/阶段2-最小需求规格.md`。

只实现三个子任务，严格按顺序：

1. 创建并自动测试可中断的 `SequencePlayer`；等待和步骤之间都必须响应停止。
2. 创建一个 JSON Hello World 宏的加载与严格校验；只接受最小规格中的字段和 `text` 步骤。
3. 将唯一宏接入现有 `HotkeyManager`；保留 F12、安全开关、鼠标窗口抑制和 Qt 主线程 UI 规则。

不得做 UI、编辑器、窗口匹配、音效、Python 脚本、鼠标/游戏动作、组合键、热键冲突检测或多宏并发。先参考 Quickinput 的 `thread.h`、`trigger.cpp` 和 ok-ww 的输入实现；所有界面测试交给用户。发现问题必须同步记录 `REVIEW_LOG.md` 与 `docs/LESSONS_LEARNED.md`，结束时创建新快照。

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
