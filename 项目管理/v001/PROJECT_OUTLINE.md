# 项目大纲 — 键盘自动化序列播放器

> 最后维护：2026-07-15 | 当前阶段：阶段0（环境初始化完成，阶段1未启动）| 操作者：Codex

本文档是项目的结构地图和进度总览。每次 AI 对话开始前必须阅读。

---

## 一、目录结构与模块状态

```
my-automation-tool/
├── main.py                      # [❌ 未创建] 程序入口
├── requirements.txt             # [✅ 已完成] pyside6, pynput, keyboard
├── config/
│   └── settings.json            # [✅ 已完成] 全局配置模板
├── src/
│   ├── __init__.py              # [✅ 已完成]
│   ├── core/
│   │   ├── __init__.py          # [✅ 已完成]
│   │   ├── input_simulator.py   # [❌ 未创建]
│   │   ├── sequence_player.py   # [❌ 未创建]
│   │   ├── script_engine.py     # [❌ 未创建]
│   │   └── hotkey_manager.py    # [❌ 未创建]
│   ├── ui/
│   │   ├── __init__.py          # [✅ 已完成]
│   │   ├── main_window.py       # [❌ 未创建]
│   │   ├── script_editor.py     # [❌ 未创建]
│   │   └── widgets/             # [❌ 未创建]
│   ├── scripts/                 # [✅ 已完成] 空目录
│   └── utils/
│       ├── __init__.py          # [✅ 已完成]
│       └── logger.py            # [✅ 已完成] logging + RotatingFileHandler
├── PROJECT_SPEC.md              # [✅ 已完成] 需求规格书
├── PROJECT_KNOWLEDGE.md         # [✅ 已完成] 优秀案例知识提取
└── PROJECT_TASKS.md             # [✅ 已完成] 任务清单
```

---

## 二、阶段进度总览

### 阶段0：环境初始化 — ✅ 100%

- [x] 所有骨架目录和文件
- [x] requirements.txt（pyside6, pynput, keyboard）
- [x] logger.py（logging + RotatingFileHandler）
- [x] settings.json 全局配置模板
- [x] PROJECT_SPEC.md / PROJECT_KNOWLEDGE.md / PROJECT_TASKS.md

### 阶段1：Hello World 验证 — ❌ 0%

- [ ] 1.1 创建 input_simulator.py（ctypes SendInput + VK_MAP）
- [ ] 1.2 创建 hotkey_manager.py（全局热键 + 焦点检测）
- [ ] 1.3 创建 main.py（PySide6 窗口 + 热键集成）
- [ ] 1.4 F9 热键触发 type_string("Hello World")
- [ ] 1.5 实测：记事本中按 F9 打出 "Hello World"
- [ ] 1.6 验证焦点检测

### 阶段2-8 — ❌ 0%

---

## 三、已确认的关键决策

| # | 决策项 | 结论 | 日期 |
|---|--------|------|------|
| 1 | 窗口最小化时热键？ | 允许触发 | 2026-07-15 |
| 2 | 全局设置保存时机？ | 退出时自动保存 | 2026-07-15 |
| 3 | 脚本报错处理？ | 非阻塞通知（2s）+ 写日志 | 2026-07-15 |

---

## 四、参考文件索引

| 文件 | 位置 | 用途 |
|------|------|------|
| 项目信心需求文档.md | 根目录 | 最高权限指令 |
| PROJECT_OUTLINE.md | 根目录（本文件） | 项目总大纲 |
| REVIEW_LOG.md | 根目录 | 审查日志 |
| PROJECT_SPEC.md | my-automation-tool/ | 需求规格书 |
| PROJECT_KNOWLEDGE.md | my-automation-tool/ | 优秀案例知识 |
| PROJECT_TASKS.md | my-automation-tool/ | 任务清单 |