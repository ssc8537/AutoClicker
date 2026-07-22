# 当前交接：Stage 19 最终归档完成

## 当前状态

用户已明确确认Stage 19D历史录像浏览、按键记录窗单行临时输入框以及此前全部功能验收通过。2026-07-23 用户再次明确授权把当前完整节点发布到GitHub默认主干`master`；发布使用普通提交，禁止强推。最终准确SHA直接读取`git log -1`或远端`refs/heads/master`，上一归档回退点仍为`a9029a8`。

当前文档只保留各自职责明确的入口：根`PRODUCT_REQUIREMENTS.md`保存当前真实需求，`PROJECT_ROADMAP.md`保存阶段状态，`README.md`与`SETUP_GUIDE.md`面向下载者，本文面向下一位AI，`native-replay/BUILDING.md`与`THIRD_PARTY_NOTICES.md`保存可复现构建和许可。`CURRENT_ACCEPTANCE.md`暂时保留本次已通过的临时输入框验收范围与明确未实现项，后续再次归档时可移除并从Git历史恢复。

当前没有自动开始的下一阶段。未来AI只在用户提出新的明确范围后继续，不得自行扩展产品。

按键记录窗底部的一次性单行临时输入框已由用户确认全部验收通过，并已重新生成`dist/MyAutoPlayer/`文件夹式便携包；用户将实际使用5–6小时后再反馈。用户另行提出“点击外部视频后仍把键盘输入送入临时框且不触发播放器快捷键”，但明确要求当前只记录、不实现；必须等用户再次授权后再处理焦点或受控输入逻辑。

## 已验收产品

- 当前唯一界面为樱空花园主题与画册侧栏，页面为宏库、触发、功能、开发连招、设置。
- Python宏入口固定为`run(player)`；单键盘/鼠标触发支持down、switch、有限次数和`COUNT=0`无限循环，停止与退出释放输入。
- OSD不抢游戏焦点，启动提示显示计划循环1次、N次或`+∞`；单实例第二次启动会唤醒并前置旧窗口。
- 开发连招完全不调用OBS：项目内Rust/WGC采集完整显示器，支持720p/1080p及15/30/45/60fps，GPU/CPU编码由用户明确选择。
- “开始”只维护压缩分段滚动缓存；“保留过往”是唯一固化入口；“停止并清空”不命名、不导出。
- 桌面声音为音轨1，可选麦克风为独立音轨2；未录像时两路真实WASAPI电平只预检、不保存。
- 全局物理按键down/up使用单调时钟记录，不读取鼠标移动、不注入游戏，并保存JSONL、CSV、前台进程证据和中文按键名称。
- 会话交付为`raw.mp4`、`raw.ass`、`input_subtitles.srt`、`events.jsonl`、`events.csv`、`metadata.json`和`native.log`；不再生成`perfect.mp4`。
- 实时按键窗口支持高亮先后色、3/5/10条事件、透明度、四角缩放、位置记忆和`HH:mm:ss:fff`本地时间；详情底部另有不落盘、关闭即清空的单行临时输入框。
- 历史录像按日期且最新在上，可播放原始视频、打开字幕/目录；删除必须选中、中文二次确认并移入Windows回收站。

## 源码与构建

- Python入口：`my-automation-tool/main.py`
- 原生核心：`my-automation-tool/native-replay/`
- 原生构建：`my-automation-tool/scripts/build_native_replay.ps1`
- 正式构建：`my-automation-tool/scripts/build_windows.ps1`
- 开发工具固定路径和卸载说明：`my-automation-tool/native-replay/BUILDING.md`
- 第三方许可：`my-automation-tool/native-replay/THIRD_PARTY_NOTICES.md`

Rust/Cargo固定为`C:\MAPL-Native-Replay\rustup\`和`C:\MAPL-Native-Replay\cargo\`，MSVC/SDK固定为`C:\MAPL-Native-Replay\vs-buildtools\`，下载缓存位于项目`.tooling/native-replay/downloads/`。这些工具不在永久系统PATH中；删除前必须提醒用户会失去重新编译能力，但不会删除源码、宏、配置、日志或视频。

## 最终自动证据

| 检查 | 结果 |
|---|---|
| Python单元测试 | 201项运行通过，7项环境跳过 |
| Rust单元测试 | 4/4通过，使用锁定离线依赖 |
| Python编译 | `python -m compileall -q .`通过 |
| 差异检查 | `git diff --check`通过，仅现有Windows CRLF提示 |
| 正式便携包 | `dist/MyAutoPlayer/MyAutoPlayer.exe`构建成功，3,059,207字节 |
| 原生核心 | 718,336字节；SHA-256 `34EA839BCD953869C67CCA20FE58237BAFA0F2B2EA60E2C6DCA6A44CE1D4C45A` |
| 打包模块 | PyInstaller xref包含`native_replay`、`input_subtitles`和`replay_history` |
| 发布隐私 | 正式包不含`replay_settings.json`、`key_monitor.json`、`ai_prompt.complete.md` |
| 残留进程 | `MyAutoPlayer`、原生录像核心、Cargo、Rustc均为0 |

发布构建不会复制本机录像保存路径、麦克风选择、窗口坐标或实时生成提示词。源码目录中的用户运行状态继续保留且被Git忽略。

两份可交付AI提示词`config/ai_prompt.md`与`config/ai_prompt.default.md`已核对为字节一致；完整第9节按键字典、动态第10/11节说明、录像事件字段、有限循环规则、双音轨与外挂字幕边界均为当前版本，本轮无需改写。

## 用户文件与已知边界

- 发布时保留用户当前宏目录的10个脚本，包括四个带`(一)/(二)`前缀的改名文件、现有脚本中文学习注释，以及新增的`macros/卡夏千9秒启动.py`；不得恢复旧文件名或旧内容。
- 中文输入法下发送的物理字母仍会进入目标窗口IME组合态；用户已接受英文完全正确、中文轻微偶发现象。
- 不支持或禁止：鼠标轨迹、滚轮自动化、OCR/图像识别、游戏内存、DLL/驱动注入、OBS运行时依赖、手柄和反作弊绕过。
- GitHub发布继续排除`build/`、`dist/`、`captures/`、日志、优秀案例源码，以及`replay_settings.json`、`key_monitor.json`、`ai_prompt.complete.md`等本机私密运行状态。
