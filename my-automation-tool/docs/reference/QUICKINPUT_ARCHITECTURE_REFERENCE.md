# Quickinput 架构参考索引

## 可借鉴的实现思想

| 子系统 | 源码证据 | 本项目适配 |
|---|---|---|
| 触发入口 | `source/src/trigger.cpp:5-102` | 先判断全局状态，再遍历可用宏；保留 F12 → F9 的安全顺序 |
| 切换与按下模式 | `trigger.cpp:70-102` | 只采用 `switch/down`；无限 down 在释放时停止 |
| 后台执行 | `source/src/thread.cpp:3-50` | 对应 `src/core/sequence_player.py` 的单实例后台轮次播放 |
| 宏库扫描 | `source/src/macro.cpp:240+` | 未来仅借鉴分组扫描概念，脚本仍为 Python |
| 主窗口失焦钩子 | `source/ui/MainUi.cpp:116-141` | 保持“鼠标在程序窗口内不触发”安全规则 |
| 页面分层 | `source/ui/MacroUi/TriggerUi/FuncUi/SettingsUi/PopsUi` | 未来拆为 `src/ui/pages`、`dialogs`、`widgets` |

## 不可复制或引入

- C++/Qt 源码、商标、JSON/QIM 存储、原版动作 DSL。
- `up` 触发模式、窗口消息注入、未验收录制、窗口匹配、音效、更新器。
- 原版“关于/更新”页及第 5 张参考图片。

遇到技术难题时先由 KnowledgeExpert 查对应源码，报告路径、行号与 Python 适配方案，不直接翻译/复制代码。
