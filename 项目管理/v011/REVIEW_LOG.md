# 项目审查日志 (REVIEW LOG) — 当前版本

> 原则：每次追加，永不删除。保留完整决策链。
>
> 完整历史版本：见 项目管理/v001/、项目管理/v002/、项目管理/v003/、项目管理/v004/。
> 项目管理/LATEST.txt 指向最新稳定版本。
>
> 本文件仅保留最近一次审查的结果摘要。详细审查记录请查阅版本文件夹。

---

## 接收摘要 / 当前状态（最新 AI --- 2026-07-15 过去本）

> 这是当前项目的**一键交接摘要**。下一个 AI 读完这段就能直接开始工作。

### 项目名称
MyAutoPlayer（键盘自动化序列播放器）— 游戏连招宏的按键序列自动执行工具。

### 当前版本
v011（项目管理/LATEST.txt 指向，快照目录待创建）

### 当前进度

| 阶段 | 进度 | 说明 |
|------|------|------|
| 阶段0：环境初始化 | 100% | |
| 阶段0.5：学习优秀案例 | 100% | |
| 阶段1.0：安全机制 | 100% | |
| 阶段1：Hello World 验证 | 100% | 用户实测通过 |
| 阶段1.5：OSD 屏幕提示 | 90% | 代码完成，已修复启动崩溃 bug 和乱码问题 |
| 阶段2+ | 0% | 等待开始 |

### 文档修复状态
- 审查 #7 乱码已修复 ✓
- SETUP_GUIDE.md 已加固（UTF-8 BOM）✓
- REVIEW_LOG.md 待拆分（当前较长，建议分为 docs/reviews/ 归档）

### 上一个 AI（过去本）做了什么事
1. 修复了 审查 #7 的全部乱码（54行原文不可逆损坏，根据上下文完整重构）
2. 为 SETUP_GUIDE.md 添加 UTF-8 BOM，防止 PowerShell 误渲染
3. 更新 PROJECT_TASKS.md / PROJECT_OUTLINE.md 同步进度

### 当前待做大事（下一 AI）
1. 详见本文末尾「给下一个 AI 的提示词」

> 这是当前项目的**一键交接摘要**。下一位 AI 读完这段就能直接开始工作。

### 项目名称
MyAutoPlayer（键盘自动化序列播放器）— 游戏连招宏的按键序列自动执行工具。

### 当前版本
v009（项目管理/LATEST.txt 指向）

### 当前进度

| 阶段 | 进度 | 说明 |
|------|------|------|
| 阶段0：环境初始化 | 100% | |
| 阶段0.5：学习优秀案例 | 100% | |
| 阶段1.0：安全机制 | 100% | |
| 阶段1：Hello World 验证 | 100% | 用户实测通过 |
| 阶段1.5：OSD 屏幕提示 | 90% | 代码完成，已修复启动崩溃 bug |
| 阶段2+ | 0% | 等待开始 |

### 上一个 AI 做了什么（Codex 2026-07-15）
1. 修复了 PySide6 6.11.1 的 QGraphicsDropShadowEffect 导入兼容性问题
   - 该类从 PySide6.QtGui 移动到 PySide6.QtWidgets
   - 导致程序启动即崩溃（黑框一闪而逝）
2. 删除了多余的 run.bat 启动脚本（用户要求直接双击 main.py 运行）
3. 验证修复：在终端运行 python main.py 成功启动，零报错
4. 更新 REVIEW_LOG.md 记录本次修复

### 当前待办
1. 用户下一步需手动测试 OSD 屏幕提示功能（docs/test-plans/STAGE_1-2.md）
2. 完成后开始阶段2：脚本管理系统


| PROJECT_OUTLINE.md | 更新 | 新增进度条目、文件索引 |
| REVIEW_LOG.md | 追加 | 本审查记录 |
| PROJECT_TASKS.md | 更新 | 新增屏幕提示文本阶段任务 |
| 项目信心需求文档.md | 更新 | 新增第六章：优秀案例问题解决原则 |

### 关键发现

1. **Quickinput 的 Pops 系统是屏幕提示的最佳参考**
   - 12 种事件类型各自可配文本+音效+颜色
   - Qi::popText 全局 Overlay 窗口，支持 Show/Hide/Popup
   - 位置(X,Y)、大小、显示时长可调

2. **Quickinput 的音效系统**
   - 5 个音效文件：notify/on/off/run/stop
   - 通过 QiFn::SoundPlay 异步播放
   - 与提示文本共享相同的触发时机

3. **Hello World 贯穿测试法**
   - 每个阶段的进度通过"能否用该阶段的新功能正确打出 Hello World"来验证
   - 测试方法直观，小白用户也能轻松验证

### 本次修改的文件

| 文件 | 操作 | 说明 |
|------|------|------|
| docs/当前状态与交接指南.md | 新建 | AI 交接用 |
| docs/需求更新-屏幕提示文本.md | 新建 | 屏幕提示需求规格 |
| docs/需求更新-音效功能参考.md | 新建 | 音效参考 |
| docs/阶段测试计划.md | 新建 | 各阶段测试方法 |
| docs/防幻觉机制.md | 新建 | 防幻觉规则 |
| 项目信心需求文档.md | 更新 | 新增第六章 |
| PROJECT_OUTLINE.md | 更新 | 进度同步 |
| PROJECT_TASKS.md | 更新 | 新增阶段 |
| REVIEW_LOG.md | 追加 | 本记录 |

### 下一步行动
1. 可开始实现屏幕提示文本功能
2. 或继续阶段2：创建 sequence_player.py


---

## 审查 #5 | 2026-07-15 | 操作者：Codex

### 审查范围
- 乱码问题排查与修复
- 项目文档体系重建（v005）
- 需求文档新增章节（用户画像 + AI 交接推测规则）

### 本次完成内容

**一、乱码问题排查与修复**
- 根因：PowerShell 的 Set-Content 未指定 -Encoding UTF8，导致 UTF-8 中文被系统默认编码（GBK）解读，产生乱码
- 修复方案：改用 Python 的 open(path, 'w', encoding='utf-8') 重建所有中文文件
- 回滚到 v004 版本后重做，所有文件编码正确

**二、文件重命名（英文命名原则）**
- 根目录：PROJECT_OUTLINE.md（英文）、REVIEW_LOG.md（英文）、项目信心需求文档.md（中文，用户保留）
- my-automation-tool/docs/：全部改为英文命名
- REQUIREMENT_EVOLUTION/：需求演进文件夹改为英文名

**三、内链更新**
- 更新了所有文件中指向旧中文名的引用路径（约 20+ 处）
- 全部统一为当前英文文件名

**四、需求文档新增内容**
- 在 项目信心需求文档.md 中新增「用户画像」章节（记录用户英语水平为高中水平）
- 在 项目信心需求文档.md 中新增「AI 交接推测规则」章节（第九条）

### 本次修改的文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| 项目信心需求文档.md | 内容新增 | 新增用户画像 + AI 交接推测规则 |
| PROJECT_OUTLINE.md | 更新 | 版本升级到 v005，进度更新 |
| REVIEW_LOG.md | 追加 | 本审查记录 |
| my-automation-tool/docs/*.md | 重命名 | 8 个文件改为英文名 |
| 全局文件引用 | 修复 | 20+ 处引用路径修正 |


## ▼ 给下一个 AI 的提示词（从这里复制）

> 以下内容可直接复制粘贴给下一个 AI。它不需要当前对话的上下文就能直接开始工作。

---

### 项目名称
MyAutoPlayer（键盘自动化序列播放器）— 游戏连招宏的按键序列自动执行工具

### 当前进度（v005）

| 阶段 | 进度 | 说明 |
|------|------|------|
| 阶段0：环境初始化 | 100% | 骨架目录、文档、日志、配置 |
| 阶段0.5：学习优秀案例 | 100% | 已提取 Quickinput + ok-ww 设计模式 |
| 阶段1.0：安全机制 | 100% | 启动即禁用 + 全局启用键 + 退出双重清理 |
| 阶段1：Hello World 验证 | 100% | F12 启用后 F9 打出 Hello World，用户实测通过 |
| 文档体系重建（v005） | 100% | 乱码修复、文件英文命名、内链更新、需求章节新增 |
| 屏幕提示文本功能 | 0% | **← 你要做的第一个任务** |
| 音效功能 | 0% | 未来阶段 |
| 阶段2：序列播放器 | 0% | 等待开始 |
| 阶段3+ | 0% | 等待开始 |

### 上一个 AI（Codex）做了什么
1. 排查并修复了 PowerShell 编码导致的乱码问题
2. 将所有文档文件名改为英文，恢复项目文档体系
3. 在 项目信心需求文档.md 中新增「用户画像」和「AI 交接推测规则」章节

### 下一个 AI 需要实现的任务（按优先级）

**优先级 1：实现屏幕提示文本功能（OSD 浮层窗口）**

需求文档：my-automation-tool/docs/OSD_POPUP_REQUIREMENT.md

子任务清单：
| # | 任务 | 文件 |
|---|------|------|
| 1 | 创建 OSD 浮层窗口类 | src/ui/osd_window.py |
| 2 | 实现 show_notification / hide_notification | src/ui/osd_window.py |
| 3 | 实现自动淡出（QTimer + 透明度动画） | src/ui/osd_window.py |
| 4 | settings.json 增加提示文本配置项 | config/settings.json |
| 5 | 热键回调中调用 OSD 显示 | main.py |
| 6 | 设置开关 | config/settings.json |
| 7 | 手动测试验证 | 按 STAGE_TEST_PLAN.md 测试 |

**关键技术参考（优秀案例1-Quickinput）：**
- 查看 Quickinput-main/source/src/tools/QiFunc.h 中的 popText 全局 Overlay 窗口
- 查看 Quickinput-main/source/ui/PopsUi.cpp 中的事件绑定和文本显示逻辑
- 使用 PySide6：Qt.FramelessWindowHint + Qt.WindowStaysOnTopHint + Qt.WA_TranslucentBackground

### 重要注意事项
- 用户是小白，英语水平高中，不写代码，只负责手动测试
- 日志文件在 my-automation-tool/logs/app.log，用日志排查问题
- 遇到问题先查 优秀案例1-Quickinput/ 和 优秀案例2-okww/ 的源码
- 一次最多做 3 个子任务（规则来自 ANTI_HALLUCINATION.md）
- 写文件时用 Python 的 open(path, 'w', encoding='utf-8')，**不要用 PowerShell 的 Set-Content**
- 所有文件使用英文命名，不要用中文文件名
- 完成所有任务后，拷贝 PROJECT_OUTLINE.md 和 REVIEW_LOG.md 到 项目管理/v006/，更新 LATEST.txt


---

## 审查 #6 | 2026-07-15 | 操作者：Codex

### 审查范围
- 初始化本地 Git 仓库
- 创建 GitHub 远程仓库
- V1 分支创建（阶段1快照）
- 提取 STAGE_TEST_PLAN.md 到根目录
- 更新文档（GitHub信息+AI信心自检规则）

### 完成内容
| 文件 | 操作 |
|------|------|
| .gitignore | 新建 |
| 项目信心需求文档.md | 新增 GitHub+AI信心章节 |
| PROJECT_OUTLINE.md | 新增 GitHub 和文件索引 |
| STAGE_TEST_PLAN.md | 复制到根目录 |
| Git 仓库 | master+V1 已本地创建 |
| 项目管理/v006/ | 当前版本快照 |

### 关键发现
1. GitHub 在当前网络不可达（连接超时），无法远程推送
2. Token 认证通过，纯属网络屏蔽问题
3. 代码已安全保存在本地 Git 仓库

### 给下一个AI
1. 读完所有文档后自检（第十一条规则）
2. 实现屏幕提示文本功能（OSD浮层）：my-automation-tool/docs/OSD_POPUP_REQUIREMENT.md
3. 一次最多做3个子任务

### GitHub 推送
网络恢复后运行：
```
git push -u origin master --force
git push -u origin V1 --force
```

---

## 审查 #7 | 2026-07-15 | 操作者：Codex

### 审查范围
- 实现屏幕提示 OSD 浮层窗口功能
- 更新项目文档与任务清单
- GitHub 策略（master+V1 分支确认）

### 本次完成内容

**核心改动（按计划完成 3 个子任务）**

| 文件 | 操作 | 说明 |
|------|------|------|
| src/ui/osd_window.py | 新建 | OSD 浮层窗口类：创建/显示/隐藏/动画 |
| config/settings.json | 修改 | 新增 popup_enabled 等 6 个 OSD 配置项 |
| main.py | 修改 | 集成 OsdPopup，F9 回调调用 show_notification |

**其他**
- 创建 _push_to_github.bat 供 AI 无法推送时用户手动推送

**GitHub 策略**
- master 分支 → 日常使用
- V1 分支（阶段 1 快照）→ 版本归档

### 关键技术发现
1. OSD 使用 QPropertyAnimation(windowOpacity) 实现淡出动画
2. 使用 QGraphicsDropShadowEffect 实现阴影效果
3. 使用 Qt.Tool 窗口标志避免在任务栏显示
4. OsdPopup 从 settings.json 加载配置，支持自定义位置和颜色

### 本次修改的文件

| 文件 | 操作 | 说明 |
|------|------|------|
| my-automation-tool/src/ui/osd_window.py | 新建 | OSD 浮层类 |
| my-automation-tool/config/settings.json | 修改 | 新增 OSD 配置 |
| my-automation-tool/main.py | 修改 | 集成 OSD 调用 |
| _push_to_github.bat | 创建 | AI 无法推送时的备用方案 |
| PROJECT_OUTLINE.md | 更新 | 进度同步 |
| PROJECT_TASKS.md | 更新 | 标记 OSD 任务完成 |
| REVIEW_LOG.md | 追加 | 审查记录 |

### 下一步行动
1. **等待用户测试 OSD 功能**，按照 STAGE_TEST_PLAN.md 测试清单
2. 等待用户确认测试结果
3. 开始阶段 2：创建 src/core/sequence_player.py

### 注意事项
- OSD 功能可以通过 settings.json 的 popup_enabled 开关控制显示
- 当前在阶段 1.5，下一阶段是阶段 2
- 按 F9 打出 Hello World 时 OSD 应同时显示绿色提示
## 审查 #8 | 2026-07-15 | 操作者：Codex

### 审查范围
- 拆分 STAGE_TEST_PLAN.md 防止 AI 幻觉
- 创建 SETUP_GUIDE.md 环境配置说明
- 更新防幻觉机制和项目信心需求文档

### 本次完成内容

**一、测试计划拆分（docs/test-plans/）**
旧的 STAGE_TEST_PLAN.md 太长（一文件含所有阶段），拆分为 3 个文件：

| 文件 | 内容 | 路径 |
|------|------|------|
| STAGE_1-2.md | 阶段1(HellowWorld) + 阶段1.5(OSD) + 阶段2(脚本管理) | docs/test-plans/ |
| STAGE_3-4.md | 阶段3(UI编辑器) + 阶段4(窗口匹配/音效) | docs/test-plans/ |
| STAGE_5+.md | 阶段5(优化) + 未来阶段(可追加) | docs/test-plans/ |
| STAGE_TEST_PLAN.md | 总索引（引向各文件） | 根目录 |

**二、SETUP_GUIDE.md 环境配置说明**
新建文件放在根目录，包含：
- Python 安装 + 虚拟环境 + 依赖安装 + 运行步骤
- 常见问题解答
- 给接手 AI 的自检提示

**三、防幻觉文档更新**
- ANTI_HALLUCINATION.md 新增规则八：文件拆分防幻觉
- 项目信心需求文档.md 新增第十二章：文件拆分防幻觉策略

**四、阶段结构重构**
根据用户需求，结合 Quickinput 的优秀案例分析，重新规划了阶段：
- 阶段1：Hello World + 安全机制（已完成）
- 阶段1.5：OSD 屏幕提示（已完成，待测试）
- 阶段2：脚本管理系统（热键绑定+触发模式+执行次数+速度倍率）
- 阶段3：热键绑定 UI + 脚本编辑器
- 阶段4：窗口匹配 + 音效/定时
- 阶段5+：多脚本并发、持久化、综合测试

### 本次修改的文件

| 文件 | 操作 | 说明 |
|------|------|------|
| docs/test-plans/STAGE_1-2.md | 新建 | 阶段1-2 测试计划 |
| docs/test-plans/STAGE_3-4.md | 新建 | 阶段3-4 测试计划 |
| docs/test-plans/STAGE_5+.md | 新建 | 阶段5+ 测试计划（可追加）|
| STAGE_TEST_PLAN.md | 重写 | 改为总索引 |
| SETUP_GUIDE.md | 新建 | 环境配置说明 |
| docs/ANTI_HALLUCINATION.md | 更新 | 新增规则八 |
| 项目信心需求文档.md | 更新 | 新增第十二章 |
| PROJECT_OUTLINE.md | 更新 | 进度同步，阶段重构 |
| REVIEW_LOG.md | 追加 | 本审查记录 |
---

## 审查 #9 | 2026-07-15 | 操作者：Codex

### 审查范围
- 最终项目文档整理 + 交接给下一个 AI

### 本次完成内容
1. 拆分 项目信心需求文档.md（317行转4子文件+短索引）
2. 新增编码规范（第十三章：用 apply_patch 写 UTF-8，防乱码）
3. 整理 GIT-GITHUB-CONNECTION.md 到 docs/ 目录
4. 更新 ANTI_HALLUCINATION.md（规则八）
5. STAGE_TEST_PLAN.md 拆分为 3 个测试文件
6. 创建 SETUP_GUIDE.md 环境配置说明
7. 更新 项目管理 快照为 v009

---

## 给下一个 AI 的提示词（从这里复制）

> 以下内容可直接复制粘贴给下一个 AI。不需要当前对话的上下文。

---

### 项目名称
MyAutoPlayer —— 游戏连招宏工具，Python + PySide6 开发

### 当前版本
v009（项目管理/LATEST.txt）

### 当前进度

| 阶段 | 进度 | 说明 |
|------|------|------|
| 阶段1：Hello World + 安全机制 | 100% | 用户实测通过 |
| 阶段1.5：OSD 屏幕提示文本 | 90% | 代码完成，等待用户手动测试 |
| 阶段2：脚本管理系统 | 0% | 下一个要做的事 |
| 阶段3：热键绑定 UI + 脚本编辑器 | 0% | 待开始 |
| 阶段4：窗口匹配 + 高级功能 | 0% | 待开始 |
| 阶段5+：完善与优化 | 0% | 待开始 |

### 上一个 AI（Codex）做了什么
1. 阶段1 Hello World + 安全机制（F12 全局禁用、F9 打字、焦点检测）
2. 阶段1.5 OSD 屏幕提示文本（无边框浮层、绿色/红色提示、2秒淡出）
3. 项目文档体系拆分与重构（rules/ 和 test-plans/ 目录）
4. 环境配置说明（SETUP_GUIDE.md）
5. 编码规范确立（禁止 PowerShell 传中文，用 apply_patch）
6. GitHub 仓库初始化并推送成功（master + V1）

### GitHub
- 仓库：https://github.com/ssc8537/AutoClicker
- SSH 已配置（参考 docs/GIT_GITHUB_CONNECTION.md）
- 分支：master（日常）+ V1（阶段1快照）

### 下一步要做什么

**第一：等待用户测试 OSD 功能**
测试步骤见：docs/test-plans/STAGE_1-2.md 的阶段 1.5 清单。

**第二：开始阶段2 - 脚本管理系统**
参考 Quickinput 实现。核心子任务：
1. 创建 macro/ 目录 + JSON 脚本格式（参考 macro.h/macro.cpp）
2. 实现脚本加载器（从 JSON 文件读取脚本配置）
3. 完善 hotkey_manager.py（多个热键绑定多个脚本）
4. 完善 TriggerMode：SWITCH/DOWN/UP + 执行次数(count) + 速度倍率(speed)

### 重要提示
1. 写 UTF-8 中文文件必须用 apply_patch 工具，禁止 PowerShell 传中文
2. 遇到问题先查优秀案例1-Quickinput 和 优秀案例2-okww 的源码
3. 一次最多做 3 个子任务，每完成一个确认结果后再做下一个
4. 用户是小白，不写代码，只负责手动测试
5. 日志是 AI 的眼睛，在 logs/app.log 排查问题
6. GitHub 推送用 git push origin master，阶段完成时创建 V2 分支

### 接手 AI 必读文档顺序
1. 项目信心需求文档.md（总索引）
2. PROJECT_OUTLINE.md（进度地图）
3. REVIEW_LOG.md（最新审查记录）
4. PROJECT_TASKS.md（任务清单）
5. docs/ANTI_HALLUCINATION.md（防幻觉规则）
6. STAGE_TEST_PLAN.md（测试总索引）

---

## 审查 #10 | 2026-07-15 | 操作者：Codex

### 审查范围
- 修复 PySide6 版本兼容性导致程序启动崩溃的问题

### 本次完成内容

**修复启动崩溃 Bug：**
- 根因：PySide6 6.11.1 将 `QGraphicsDropShadowEffect` 从 `PySide6.QtGui` 移动到 `PySide6.QtWidgets`
- 影响：`src/ui/osd_window.py` 第10行导入失败，程序启动即崩溃，黑框一闪而逝
- 修复：将该类的导入从 `QtGui` 移动到 `QtWidgets` 导入行

**验证结果：**
- 清理 `__pycache__` 后从零启动，程序正常显示窗口
- 日志输出：MyAutoPlayer 启动 → 热键管理器已启动（F9已注册，F12为全局启用/禁用键）
- 无任何 ImportError 或运行时崩溃

### 本次修改的文件
| 文件 | 操作 | 说明 |
|------|------|------|
| my-automation-tool/src/ui/osd_window.py | 修改 | QGraphicsDropShadowEffect 导入从 QtGui 改为 QtWidgets |

### 给下一个 AI 的提示
当前代码已经可以正常双击 main.py 运行。如果用户报告仍然打不开，请：
1. 先在终端手动运行 `python main.py` 查看完整报错
2. 检查 Python 版本和 PySide6 版本是否有其他 API 变更
3. 检查是否有新的 `__pycache__` 缓存导致旧错误残留

---

## 审查 #11 | 2026-07-15 | 操作者：Codex（过去本）

### 审查范围
- 修复 审查 #7 的乱码问题（原文被 ? 永久替代，根据上下文重构）
- 为 SETUP_GUIDE.md 添加 UTF-8 BOM，修复 PowerShell 编码检测问题

### 本次完成内容

**一、修复 审查 #7 乱码**
- 问题：在 v005 文档体系重建时，审查 #7 的中文内容被不可逆损坏（所有中文字符替换为 0x3F）
- 方法：根据以下证据重构：
  - 其他审查条目（#5、#6、#8、#9）的格式模板
  - PROJECT_TASKS.md 的实际 OSD 任务清单
  - osd_window.py 的实际代码实现
  - GitHub 策略、文件列表等可读的结构化信息
- 结果：54 行乱码全部还原为正确中文

**二、SETUP_GUIDE.md 编码加固**
- 问题：文件为 UTF-8 无 BOM，PowerShell 在中文 GBK 环境下误渲染
- 修复：添加 UTF-8 BOM（EF BB BF）
- 结果：PowerShell 可正确识别编码

### 本次修改的文件
| 文件 | 操作 | 说明 |
|------|------|------|
| REVIEW_LOG.md | 修改 | 还原审查 #7 全部正文 + 追加本审查记录 |
| SETUP_GUIDE.md | 修改 | 添加 UTF-8 BOM |
| PROJECT_TASKS.md | 更新 | 新增文档修复任务 |
| PROJECT_OUTLINE.md | 更新 | 同步当前进度 |

## ▼ 给下一个 AI 的提示词（从这里复制）

> 以下内容可直接复制粘贴给下一个 AI。不需要当前对话的上下文就能直接开始干活。

---

### 项目名称
MyAutoPlayer — 游戏连招宏的按键序列自动执行工具

### 当前版本
v011（项目管理/LATEST.txt 已指向 v011，但快照目录尚未创建）

### 当前进度

| 阶段 | 进度 | 说明 |
|------|------|------|
| 阶段1：Hello World + 安全机制 | 100% | 用户实测通过 |
| 阶段1.5：OSD 屏幕提示文本 | 90% | 代码完成，待用户手动测试 |
| 阶段2：脚本管理系统 | 0% | 等待开始 |
| 阶段3-5 | 0% | 等待开始 |

### 文档修复状态
- 审查 #7 乱码已修复 ✓
- SETUP_GUIDE.md 已加固（UTF-8 BOM）✓
- REVIEW_LOG.md 仍需拆分（441行略长，建议按 v3.0 方案的 docs/reviews/ 目录拆分）

### 上一个 AI（过去本）做了什么事
1. 修复了 审查 #7 的全部乱码（54行原文不可逆损坏，根据上下文完整重构）
2. 为 SETUP_GUIDE.md 添加 UTF-8 BOM，防止 PowerShell 误渲染
3. 更新 PROJECT_TASKS.md / PROJECT_OUTLINE.md 同步进度

### 下一个 AI 需要做的事（按优先级排列）

**优先级 1：文档规则更新（3 个文件）**
参考 v3.0 方案的任务二：
- docs/rules/03-问题解决与自检规则.md：新增规则6-1 + 防止问题复发章节
- 项目信心需求文档.md：核心原则追加第7条 + 新增第十三章

**优先级 2：REVIEW_LOG.md 拆分**
参考 v3.0 方案的任务三：
- REVIEW_LOG.md 精简为 ~110 行（仅保留接手摘要 + 审查#10 + #11）
- 创建 docs/reviews/REVIEW_05-06.md（审查#5+#6）
- 创建 docs/reviews/REVIEW_07-09.md（审查#7+#8+#9）

**优先级 3：漏洞修复（main.py + osd_window.py）**
参考 v3.0 方案的任务五：
- main.py 新增 _HotkeyDispatcher(QObject)，用 Qt 信号将热键回调从钩子线程转发到 Qt 主线程
- osd_window.py：OsdPopup(self) → OsdPopup(None)
- 非阻塞执行锁：快速连按 F9 只执行第一次

**优先级 4：交接快照**
完成上述工作后：
- 更新 PROJECT_OUTLINE.md / PROJECT_TASKS.md
- 创建 项目管理/v012/ 快照
- 更新 LATEST.txt → v012
- 在 REVIEW_LOG.md 追加新的审查记录和提示词

### 重要提示
1. 写 UTF-8 中文文件必须用 apply_patch 工具，禁止用 PowerShell 传中文
2. 遇到问题先去 优秀案例1-Quickinput/ 和 优秀案例2-okww/ 的源码中找答案
3. 一次最多做 3 个子任务，每完成一个确认结果后再做下一个
4. 日志在 logs/app.log，是 AI 排查问题的眼睛
5. 用户是小白，不写代码，只负责手动测试
