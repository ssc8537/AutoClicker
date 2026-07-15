# 项目审查日志 (REVIEW LOG)

> 原则：每次追加，永不删除。保留完整决策链。

---

## 2026-07-15 审查 #1 | 操作者：Codex

### 审查范围

- 读取全部需求文档：`1.md`、`2.md`、`3.md`、`4.md`、`项目信心需求文档.md`
- 审查 `my-automation-tool/` 下所有现有文件：logger.py、settings.json、__init__.py、PROJECT_SPEC.md、PROJECT_KNOWLEDGE.md、PROJECT_TASKS.md
- 审查两个优秀案例的知识提取文档（PROJECT_KNOWLEDGE.md 中记录的代码模式）

### 进度审查结论

| 状态 | 项目 | 说明 |
|------|------|------|
| ✅ 已完成且合格 | 项目骨架目录 | 所有子目录和 __init__.py 已创建 |
| ✅ 已完成且合格 | requirements.txt | pyside6, pynput, keyboard 已写入 |
| ✅ 已完成且合格 | logger.py | logging + RotatingFileHandler，控制台+文件双输出，线程安全 |
| ✅ 已完成且合格 | settings.json | 全局配置模板 |
| ✅ 已完成且合格 | PROJECT_SPEC.md | 完整的模块接口定义、数据格式、按键映射 |
| ✅ 已完成且合格 | PROJECT_KNOWLEDGE.md | SendInput 骨架、Quickinput 状态机分发、线程模型、WndMatch、避坑指南均已提取 |
| ✅ 已完成且合格 | PROJECT_TASKS.md | 任务粒度合理，阶段拆分清晰 |
| ❌ 未开始 | 所有核心模块 | input_simulator.py、hotkey_manager.py、sequence_player.py、script_engine.py 均未创建 |
| ❌ 未开始 | 所有 UI 模块 | main_window.py、script_editor.py 均未创建 |
| ❌ 未开始 | main.py 入口 | 未创建 |
| ❌ 未开始 | Hello World 验证 | 整个阶段1未启动 |

### 已识别风险

| 风险 | 严重度 | 缓解措施 |
|------|--------|----------|
| `keyboard` 库在某些系统被安全软件拦截 | 🟡 中 | 提供 pynput fallback；告知用户添加白名单 |
| SendInput 在部分游戏被反作弊屏蔽 | 🟡 中 | ok-ww 已验证可行性 |
| 多脚本并发时键盘输入交错导致游戏行为异常 | 🔵 低 | 由用户自行保证脚本逻辑不冲突 |
| Python 脚本中 `import` 恶意模块或无限循环 | 🟡 中 | daemon thread 执行 + stop_event + 全局禁用键兜底 |

### 遗留问题（审查 #1 时）

- [x] 根目录 1.md ~ 4.md 散乱 → 审查 #2 已归档到 docs/需求演进/
- [ ] 多脚本并发时按键优先级/锁机制未定义
- [ ] 脚本 `.meta.json` 与脚本文件双文件管理同步问题
- [ ] `window_match` 通配符窗口匹配未实现

### 本次确认的决策

| # | 问题 | 结论 | 影响模块 |
|---|------|------|----------|
| 1 | 窗口最小化时热键是否触发？ | **允许触发** | hotkey_manager.py |
| 2 | 全局设置何时保存？ | **退出时自动保存** | main_window.py |
| 3 | Python 脚本报错如何处理？ | **非阻塞通知（2s 消失）+ 写日志** | script_engine.py |

### 下一步行动（审查 #1 后）

1. 进入**阶段1**：创建 `input_simulator.py` → `hotkey_manager.py` → `main.py` → Hello World 实测
2. 整理根目录散乱文档
3. 更新 `src/utils/__init__.py` 暴露 logger API

---

## 2026-07-15 审查 #2 | 操作者：Codex

### 审查范围

- 重新读取全部项目文件和文档
- 审查上轮遗留问题的处理状态
- 审查新创建的三个核心模块代码
- 验证合并操作完成情况

### 本次完成的操作

1. **文件合并**：将 `优秀案例1-Quickinput/`、`优秀案例2-okww/` 移入 `my-automation-tool/`；将 `1-4.md` 归档到 `docs/需求演进/`。

2. **路径修正**：`PROJECT_SPEC.md` 中参考案例路径从 `../优秀案例` 改为 `./优秀案例`。

3. **阶段1 代码创建**（Hello World 验证）：
   - `src/core/input_simulator.py` — ctypes SendInput 完整封装（60+ 键 VK_MAP、tap/press/release/hold、click/mouse_down/mouse_up、Unicode type_string）
   - `src/core/hotkey_manager.py` — 全局热键管理（keyboard 库）、焦点检测、三种触发模式状态机、全局禁用开关
   - `main.py` — PySide6 入口（QMainWindow + F9 热键集成 + Hello World 回调 + 管理员权限检测）

### 进度审查结论

| 状态 | 项目 | 说明 |
|------|------|------|
| ✅ 已完成且合格 | 文件合并 | 6 项全部移动到 my-automation-tool/ |
| ✅ 已完成且合格 | 阶段0 | 100% |
| ✅ 已完成且合格 | 阶段1 编码 | 1.1-1.4 全部完成 |
| ⏳ 待实测 | 阶段1 验证 | 1.5 记事本打字测试、1.6 焦点检测测试（需安装 PySide6 后运行）|

### 代码审查发现（审查 #2 新增）

| 文件 | 严重级 | 问题 | 建议 |
|------|--------|------|------|
| `input_simulator.py` | 🔵 建议 | VK_MAP 未包含 "minus"/"equals"/"comma" 等符号键 | 如用户需要再补充，当前 60+ 键覆盖游戏常用按键 |
| `input_simulator.py` | 🔵 建议 | 缺少 pynput fallback | 阶段2 完善 input_simulator 时补充 |
| `hotkey_manager.py` | 🟡 警告 | UP 模式未完整实现——仅限于 PRESS 和 SWITCH | 阶段4 完善热键管理时补充 |
| `hotkey_manager.py` | 🔵 建议 | 多脚本并发时的热键注册未做冲突检测 | 阶段4 热键冲突检测时补充 |
| `main.py` | 🔵 建议 | 管理员权限检测仅打印警告，未弹窗提示用户 | 阶段4 收尾时加入 UI 提示 |

### 当前风险

| 风险 | 严重度 | 状态 |
|------|--------|------|
| keyboard 库 hook 与 PySide6 事件循环兼容性 | 🟡 中 | 待实测验证 |
| PySide6 未安装 | 🟡 中 | 安装进行中 |
| F9 被其他程序占用 | 🔵 低 | 用户可自行换键 |

### 下一步行动

1. 安装 PySide6 依赖
2. 运行 main.py → 实测 F9 打出 Hello World
3. 实测焦点检测：鼠标在窗口内时 F9 不触发
4. 实测通过后进入阶段2：创建 sequence_player.py

---

**下一位 AI 接手时，请先阅读：**
1. `项目信心需求文档.md`（最高指令）
2. `PROJECT_OUTLINE.md`（进度地图）
3. `REVIEW_LOG.md`（本文件，了解历史审查和风险）
4. `my-automation-tool/PROJECT_SPEC.md`（需求规格书）
5. `my-automation-tool/PROJECT_KNOWLEDGE.md`（技术知识）
