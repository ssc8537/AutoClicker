# 项目总控任务清单

> 项目名称：键盘自动化序列播放器 (MyAutoPlayer) | 最后更新：2026-07-15（审查 #12 后）

---

## 阶段0：环境初始化

- [x] 0.1 创建项目根目录和所有子目录结构
- [x] 0.2 创建 requirements.txt
- [x] 0.3 创建所有 __init__.py 空文件
- [x] 0.4 创建 src/utils/logger.py
- [x] 0.5 复制参考项目到项目目录下
- [x] 0.6 创建 PROJECT_SPEC.md
- [x] 0.7 创建 config/settings.json 模板
- [x] 0.8 重写 PROJECT_KNOWLEDGE.md
- [x] 0.9 创建根目录 PROJECT_OUTLINE.md
- [x] 0.10 创建根目录 REVIEW_LOG.md
- [x] 0.11 更新 src/utils/__init__.py

## 阶段0.5：学习优秀案例

- [x] 0.5.1 全面浏览两个优秀案例的目录结构
- [x] 0.5.2 深入阅读输入模拟代码
- [x] 0.5.3 深入阅读热键绑定与焦点检测代码
- [x] 0.5.4 分析 UI 设计与交互模式
- [x] 0.5.5 分析线程管理模型
- [x] 0.5.6 分析窗口匹配模型
- [x] 0.5.7 生成完善版 PROJECT_KNOWLEDGE.md

## 阶段1.0：安全机制

- [x] 1.0.1 hotkey_manager.py：_global_disabled 默认值 False -> True
- [x] 1.0.2 hotkey_manager.py：完善 toggle_global_disabled + on_toggle
- [x] 1.0.3 main.py：_setup_ui 增加状态指示标签
- [x] 1.0.4 main.py：_setup_hotkey 注册 F12 全局切换键
- [x] 1.0.5 main.py：closeEvent + atexit 双重清理
- [x] 1.0.6 自动验证通过

## 阶段1：Hello World 验证

- [x] 1.1 创建 src/core/input_simulator.py
- [x] 1.2 创建 src/core/hotkey_manager.py
- [x] 1.3 创建 main.py
- [x] 1.4 F9 热键触发 type_string("Hello World")
- [x] 1.5 用户手动实测：F12 启用后 F9 打出 Hello World（通过）
- [x] 1.6 焦点检测：鼠标在窗口内时 F9 不触发

---

## 屏幕提示文本功能（新需求，已记录规格）

- [x] 2.1 创建 src/ui/osd_window.py（OSD 浮层窗口）
- [x] 2.2 实现 show_notification / hide_notification
- [x] 2.3 实现自动淡出
- [x] 2.4 settings.json 增加提示文本配置项
- [x] 2.5 热键回调中调用 OSD 显示
- [x] 2.6 设置开关
- [ ] 2.7 手动测试验证
- [x] 2.8 修复审查记录乱码（审查 #7 完整重构还原）
- [x] 2.9 文档编码加固（SETUP_GUIDE.md 添加 UTF-8 BOM）
- [x] 2.10 修复热键钩子跨线程访问与 F9 连按重叠漏洞

## 阶段2：序列播放器

- [ ] 3.1 完善 input_simulator.py
- [ ] 3.2 创建 src/core/sequence_player.py
- [ ] 3.3 支持中断控制
- [ ] 3.4 支持速度倍率

## 阶段3：脚本引擎

- [ ] 4.1 创建 src/core/script_engine.py
- [ ] 4.2 实现 ScriptPlayer API
- [ ] 4.3 实现 JSON 配置脚本解析
- [ ] 4.4 支持执行次数和循环间隔

## 阶段4：完整热键管理

- [ ] 5.1 完善 hotkey_manager.py（多键绑定、冲突检测）
- [ ] 5.2 实现三种触发模式
- [ ] 5.3 实现全局禁用热键

## 阶段5：主 UI 界面

- [ ] 6.1 创建 src/ui/main_window.py（Quickinput 风格）
- [ ] 6.2 创建 src/ui/script_editor.py
- [ ] 6.3 热键绑定输入框
- [ ] 6.4 执行次数设置
- [ ] 6.5 速度倍率滑块
- [ ] 6.6 状态栏提示

## 阶段6-8

- [ ] 7.1 QThread 执行脚本
- [ ] 7.2 紧急停止按钮
- [ ] 7.3 多脚本并发执行
- [ ] 7.4 脚本错误捕获
- [ ] 7.5 配置持久化
- [ ] 7.6 完整功能测试

---

规则：一次对话最多执行 3 个子任务。每完成一项将 [ ] 改为 [x]。
