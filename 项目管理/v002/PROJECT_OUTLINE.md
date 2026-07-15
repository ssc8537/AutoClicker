# 项目大纲 — 键盘自动化序列播放器

> 最后维护：2026-07-15 | 当前阶段：阶段1（Hello World 验证 — 代码已就绪，待实测）| 操作者：Codex

本文档是项目的结构地图和进度总览。每次 AI 对话开始前必须阅读。
与 `项目信心需求文档.md` 同级，方便用户实时查看进度。

---

## 一、目录结构与模块状态

```
my-automation-tool/
├── main.py                      # [✅ 已完成] 程序入口（PySide6 窗口 + F9 热键）
├── requirements.txt             # [✅ 已完成] pyside6, pynput, keyboard
├── config/
│   └── settings.json            # [✅ 已完成] 全局配置模板
├── docs/
│   ├── MERGE_LOG.md             # [✅ 已完成] 文件合并记录
│   └── 需求演进/                 # [✅ 已完成] 1-4.md 需求迭代历史
├── src/
│   ├── __init__.py              # [✅ 已完成]
│   ├── core/
│   │   ├── __init__.py          # [✅ 已完成]
│   │   ├── input_simulator.py   # [✅ 已完成] SendInput API 封装（VK_MAP + tap/press/release/click/type）
│   │   ├── sequence_player.py   # [❌ 未创建] 序列执行器（可中断+倍速）
│   │   ├── script_engine.py     # [❌ 未创建] 脚本加载与执行
│   │   └── hotkey_manager.py    # [✅ 已完成] 热键管理+焦点检测+三种触发模式+全局禁用
│   ├── ui/
│   │   ├── __init__.py          # [✅ 已完成]
│   │   ├── main_window.py       # [❌ 未创建] 主窗口 UI
│   │   ├── script_editor.py     # [❌ 未创建] 脚本编辑对话框
│   │   └── widgets/             # [❌ 未创建] 自定义控件目录
│   ├── scripts/                 # [✅ 已完成] 用户脚本目录（空）
│   └── utils/
│       ├── __init__.py          # [✅ 已完成] re-export get_logger, setup_logging
│       └── logger.py            # [✅ 已完成] logging + RotatingFileHandler
├── 优秀案例1-Quickinput/         # [✅ 已完成] UI风格参考
├── 优秀案例2-okww/               # [✅ 已完成] 输入模拟参考
├── PROJECT_SPEC.md              # [✅ 已完成] 需求规格书
├── PROJECT_KNOWLEDGE.md         # [✅ 已完成] 优秀案例知识提取
└── PROJECT_TASKS.md             # [✅ 已完成] 任务清单
```

---

## 二、阶段进度总览

### 阶段0：环境初始化 — ✅ 100%

- [x] 所有骨架目录和文件
- [x] 优秀案例移入项目目录
- [x] 需求文档 1-4.md 归档到 docs/需求演进/

### 阶段1：Hello World 验证 — ✅ 代码就绪，待实测

- [x] 1.1 input_simulator.py（ctypes SendInput + 60+键 VK_MAP + type_string）
- [x] 1.2 hotkey_manager.py（全局热键 + 焦点检测 + 三种触发模式 + 全局禁用）
- [x] 1.3 main.py（PySide6 窗口 + 集成热键 + 管理员权限检测）
- [x] 1.4 F9 热键触发 type_string("Hello World")
- [ ] 1.5 实测：光标在记事本中按 F9 打出 "Hello World"
- [ ] 1.6 验证焦点检测：鼠标在程序窗口内时 F9 不触发

### 阶段2：脚本执行引擎 — ❌ 0%

### 阶段3：UI 与配置持久化 — ❌ 0%

### 阶段4：多脚本并发与收尾 — ❌ 0%

---

## 三、已确认的关键决策

| # | 决策项 | 结论 | 日期 |
|---|--------|------|------|
| 1-13 | （同 PROJECT_SPEC.md 第八节） | 略 | 前期/2026-07-15 |

---

## 四、参考文件索引

| 文件 | 位置 | 用途 |
|------|------|------|
| 项目信心需求文档.md | 根目录 | 最高权限指令，AI 接手第一步阅读 |
| PROJECT_OUTLINE.md | 根目录（本文件） | 项目总大纲，进度地图 |
| REVIEW_LOG.md | 根目录 | 审查日志，持续追加 |
| PROJECT_SPEC.md | my-automation-tool/ | 需求规格书，模块接口定义 |
| PROJECT_KNOWLEDGE.md | my-automation-tool/ | 优秀案例知识提取 |
| PROJECT_TASKS.md | my-automation-tool/ | 任务清单与进度跟踪 |
| docs/需求演进/1-4.md | my-automation-tool/docs/ | 原始需求记录（已归档） |
| docs/MERGE_LOG.md | my-automation-tool/docs/ | 文件合并记录 |

---

**本文档随项目进展实时更新。每次 AI 对话前必须阅读。**
