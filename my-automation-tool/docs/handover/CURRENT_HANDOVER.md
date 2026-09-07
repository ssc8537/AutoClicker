# 当前交接：Stage 22 滚轮滑动触发等待用户验收

## 当前状态

2026-09-07 Stage 22 实现完成：触发页“触发详情（自动保存）”底部新增“滚轮滑动”勾选框。勾选后该宏只由滚轮触发，滑满一格（±120，上滑/下滑等价）产生一次触发脉冲，统一切换语义（滑一格启动、再滑一格停止，与宏的 MODE 无关）；原热键输入框变灰失效但保留值，触发列表热键列显示“滚轮”；取消勾选立即恢复原热键。宏文件新增可选 `WHEEL = True/False`（默认 False），`HOTKEY` 字段明确拒绝滚轮。

实现链路：`src/core/input_keys.py` 定义 `WHEEL_HOTKEYS` 与“滚轮”显示名；`src/core/macro_library.py` 的 `MacroMetadata` 新增 `wheel: bool = False` 并校验；`src/core/macro_file_manager.py` 原子保存 WHEEL；`src/core/hotkey_manager.py` 在 Windows 低级鼠标钩子中识别 `WM_MOUSEWHEEL`(0x020A)，从 `mouseData` 高 16 位读取 delta，满一格发一次 down+up 脉冲进入统一 FIFO（MAPL 标记过滤不变）；`main.py` 勾选互斥、把滚轮宏注册为 `("wheel", switch)` 绑定。

案例证据：`优秀案例1-Quickinput/Quickinput-main/source/src/tools/ihook.h:7-8`（VK_WHEELUP/VK_WHEELDOWN）与 `:47-48`（`WM_MOUSEWHEEL` 高 16 位 ≥0x78 / ≤0xFF88 发一次脉冲）。案例把上滑/下滑当两个独立绑定；本项目按需求统一为同一“滚轮”触发，属于有意适配，不是偏差。

自动证据：2026-09-07 重跑 `py -m unittest discover -s tests`，224 项通过、7 项环境跳过；正式便携包 `dist/MyAutoPlayer/MyAutoPlayer.exe` 已于 16:33 重建（2,747,497 字节），晚于全部源码改动（16:26 前）。用户 2026-09-07 授权后已普通推送 `62b861a` 到 GitHub 默认主干 `master`（远端 SHA 核验一致，随源码一并同步了用户当前宏库：异环/鸣潮/自动剧情三个新宏、两处宏改名和压枪宏的起始平A改动；`macros.zip` 已加入 `.gitignore` 不上传）。**当前唯一下一步是用户按 `my-automation-tool/CURRENT_ACCEPTANCE.md` 进行 Windows 人工验收；用户明确说通过前不得写“已验收”。**

## Stage 21 归档状态（历史）

2026-08-14 用户确认 Stage 21 全部验收通过。项目新增只读 `player.is_physical_pressed(key)`：它读取 Windows 全局钩子确认的真实物理 down/up，程序自身带 `MAPL` 标记的模拟输入不会写入该状态。`macros/z-完美压枪宏.py` 保持 `HOTKEY='backslash'`，使用 `MODE='switch'`、`COUNT=0`：按一次反斜杠开启监听；物理左键未按时低频等待，按住时执行压枪，松开后停止移动并继续等待；再按一次反斜杠完全停止。

压枪算法没有改成新曲线。自动对比确认当前宏与 `macros/z-完美压枪宏-初版.py` 的九组参数完全一致：500/800/800ms 三阶段、左右随机、向下随机、下压随机2、间隔随机(-2/0/2)、每8步点射重置、100ms、重置随机10ms、扇形基准4.0。点射等待期间若物理左键已经松开，不会再次模拟按下。这里的“8”是八次下压步骤，不是读取游戏弹药后的真实八发；项目仍不读取游戏内存、武器或弹药状态。

完整自动测试为217项通过、7项环境跳过；标准 `dist/MyAutoPlayer/MyAutoPlayer.exe` 已重建，包内宏与源码SHA-256一致。用户授权将当前完整节点普通推送到GitHub默认主干`master`，禁止强推。

## Stage 20 归档状态（历史）

Stage 20 已完成源码、自动测试、文档同步、正式便携 EXE 构建和 Windows 11 人工验收。最终公开 API 为 `player.mouse_move(x, y, duration_ms=0)`：x/y 是相对当前光标的整数位移（X 正数向右、Y 正数向下），范围 -10000–10000；duration_ms 为 0–10000，0 表示一次发送，大于 0 表示约 10ms 分步平滑移动，真实移动时长不受 SPEED 缩放。停止、down 松开、switch 再按、全局禁用和退出都会阻止后续步骤。

用户无法用原四方向教程直接验收后，本轮已续写 `macros/z-自动压枪宏.py` 作为最简可运行验收脚本：保留用户的 `backslash`/`down` 元数据并启用；按住触发键时 `mouse_down("left")`，以固定每15ms向下1单位的节奏移动，松开或停止后在 `finally` 释放左键。当前明确没有随机化、武器识别或反作弊规避。

开发连招页另新增“麦克风预检”独立开关，每次程序启动默认关闭。关闭时 Python 控制器向原生核心传 `--record-microphone false`，Rust `AudioRuntime` 不创建麦克风采集源；桌面声音预检仍继续。用户主动开启后才以 `true` 重启预检并读取所选麦克风。此开关只控制空闲预检，正式录像的独立麦克风音轨仍由“录制麦克风声音”设置决定。

优秀案例 1 的只读证据位于 `my-automation-tool/优秀案例1-Quickinput/Quickinput-main/source/src/tools/input.h:63-76` 与 `source/src/interpreter.cpp:236-285`：相对移动使用 `MOUSEEVENTF_MOVE` 和 `MOUSEINPUT(dx, dy)`，绝对位置另有独立接口；`source/src/func.cpp:139-167` 使用整数累计分步，解释“移动”UI 与约 10ms 节奏。本项目仅适配相对行为，不复制 C++、案例格式、绝对坐标、轨迹或滚轮能力。

用户已明确确认Stage 19D历史录像浏览、按键记录窗单行临时输入框以及此前全部功能验收通过。2026-07-23 用户再次明确授权把当前完整节点发布到GitHub默认主干`master`；发布使用普通提交，禁止强推。最终准确SHA直接读取`git log -1`或远端`refs/heads/master`，上一归档回退点仍为`a9029a8`。

当前文档只保留各自职责明确的入口：根`PRODUCT_REQUIREMENTS.md`保存当前真实需求，`PROJECT_ROADMAP.md`保存阶段状态，`README.md`与`SETUP_GUIDE.md`面向下载者，本文面向下一位AI，`native-replay/BUILDING.md`与`THIRD_PARTY_NOTICES.md`保存可复现构建和许可。`CURRENT_ACCEPTANCE.md`保存当前待验收的滚轮滑动触发教程（Stage 21 压枪教程已被替换，验收结论保留在 Stage 21 归档段）。

2026-07-23用户实际使用后报告五项问题。本轮已实现：临时框聚焦时仅抑制宏触发/全局切换/OSD并继续保留录像旁路日志；最小化按键窗再次点击按钮会`showNormal()`恢复；桌面音轨新增0–300%增益并贯穿预检、正式录制和元数据；顶部时钟使用详情字号约2倍；30分钟导出改用单个UTF-8合并清单，不再把约180组视频/音频绝对路径放入Windows命令行。用户已确认验收教程全部通过，并授权把当前完整节点普通提交、推送到GitHub默认主干`master`。

当前没有自动开始的下一阶段。未来AI只在用户提出新的明确范围后继续，不得自行扩展产品。

本轮新增修改：`src/core/physical_input_state.py` 保存经钩子过滤后的真实物理状态；`src/core/hotkey_manager.py` 更新并在停止时清空状态；`src/core/script_player.py` 公开只读查询；AI提示词、需求、路线图、测试和验收文档同步更新。归档发布时保留宏目录当前的新增、修改、改名、分组和删除状态，不恢复旧文件名或旧内容，也不上传重复压缩备份。

按键记录窗底部的一次性单行临时输入框已由用户确认全部验收通过，并已重新生成`dist/MyAutoPlayer/`文件夹式便携包；用户将实际使用5–6小时后再反馈。用户另行提出“点击外部视频后仍把键盘输入送入临时框且不触发播放器快捷键”，但明确要求当前只记录、不实现；必须等用户再次授权后再处理焦点或受控输入逻辑。

## 已验收产品

- 当前唯一界面为樱空花园主题与画册侧栏，页面为宏库、触发、功能、开发连招、设置。
- Python宏入口固定为`run(player)`；单键盘/鼠标触发支持down、switch、有限次数和`COUNT=0`无限循环，停止与退出释放输入。
- OSD不抢游戏焦点，启动提示显示计划循环1次、N次或`+∞`；单实例第二次启动会唤醒并前置旧窗口。
- 开发连招完全不调用OBS：项目内Rust/WGC采集完整显示器，支持720p/1080p及15/30/45/60fps，GPU/CPU编码由用户明确选择。
- “开始”只维护压缩分段滚动缓存；“保留过往”是唯一固化入口；“停止并清空”不命名、不导出。
- 桌面声音为音轨1，可选麦克风为独立音轨2；桌面增益0–300%默认150%，未录像时两路真实WASAPI电平只预检、不保存。
- 全局物理按键down/up使用单调时钟记录，不读取鼠标移动、不注入游戏，并保存JSONL、CSV、前台进程证据和中文按键名称。
- 会话交付为`raw.mp4`、`raw.ass`、`input_subtitles.srt`、`events.jsonl`、`events.csv`、`metadata.json`和`native.log`；不再生成`perfect.mp4`。
- 实时按键窗口支持高亮先后色、3/5/10条事件、透明度、四角缩放、位置记忆和放大后的`HH:mm:ss:fff`本地时间；详情底部另有不落盘、关闭即清空的单行临时输入框。临时框聚焦时不启动宏或刷新实时状态，最小化后可由开发连招页重新恢复。
- 历史录像按日期且最新在上，可播放原始视频、打开字幕/目录；删除必须选中、中文二次确认并移入Windows回收站。

## 源码与构建

- Python入口：`my-automation-tool/main.py`
- 原生核心：`my-automation-tool/native-replay/`
- 原生构建：`my-automation-tool/scripts/build_native_replay.ps1`
- 正式构建：`my-automation-tool/scripts/build_windows.ps1`
- 开发工具固定路径和卸载说明：`my-automation-tool/native-replay/BUILDING.md`
- 第三方许可：`my-automation-tool/native-replay/THIRD_PARTY_NOTICES.md`

Rust/Cargo固定为`C:\MAPL-Native-Replay\rustup\`和`C:\MAPL-Native-Replay\cargo\`，MSVC/SDK固定为`C:\MAPL-Native-Replay\vs-buildtools\`，下载缓存位于项目`.tooling/native-replay/downloads/`。这些工具不在永久系统PATH中；删除前必须提醒用户会失去重新编译能力，但不会删除源码、宏、配置、日志或视频。

## Stage 20 自动证据

| 检查 | 结果 |
|---|---|
| 案例证据 | `优秀案例1.../source/src/tools/input.h:63-76` 与 `source/src/interpreter.cpp:236-285` 已核对；相对移动使用 `MOUSEEVENTF_MOVE`/`dx/dy`，不适配绝对位置和轨迹。 |
| Stage 20 定向测试 | 播放器 15 项、底层输入 9 项通过；压枪宏假输入顺序为左键down→向下移动→中断→左键up；测试不真实移动鼠标。 |
| 麦克风预检 | 原生控制器13项、UI 49项通过（6项环境跳过）；默认 false 与手动 true 参数均覆盖，关闭后桌面声音预检继续。 |
| 本轮正式便携包 | 用户关闭旧程序后，标准 `dist/MyAutoPlayer/` 已重新构建成功；临时构建目录已清理。 |
| 新包核验 | 标准 EXE 3,067,880 字节，SHA-256 `F03AE5EFC145364AB7219E1518A69D3CA77A5E72692C753B17FEFFB641248BC4`；原生核心 726,016 字节，源码 release 与包内 SHA-256 均为 `2B088D215FFA52229279CA5F7BD1819969DB267C3CA38219230D79ADE360B1C1`；包内压枪宏和两份 AI 提示词均与源码字节一致，私密运行状态 0 项，构建后无相关残留进程。 |
| 产品回归 | 排除用户宏固定快照后 210 项通过、7 项环境跳过；AI 提示词 7 项、UI 48 项通过。完整套件另有 9 项旧宏快照失败，原因是用户当前宏已改名/删除/改键/改循环，本轮未恢复或改动。 |
| Python 编译 | `main.py`、`src`、`tests` compileall 通过。 |
| 差异检查 | `git diff --check` 通过（用户宏未纳入本轮检查范围）。 |
| 正式便携包 | `dist/MyAutoPlayer/MyAutoPlayer.exe`，3,065,582 字节；SHA-256 `490372FBDC2DA8E1E6B30F554F2941D78305173A92F5D4C1C53B14C640F0D343`。 |
| 原生核心 | 725,504 字节；源码 release 与包内 SHA-256 均为 `5B2E0A39F8D46D8B2E562371D6F449E1D00CF1C965466CCF420E55725E15B1E2`。 |
| 发布隐私 | 包内无 `replay_settings.json`、`key_monitor.json`、`ai_prompt.complete.md`；构建后 MyAutoPlayer、原生核心、Cargo、Rustc 残留进程为 0。 |

## 最终自动证据

| 检查 | 结果 |
|---|---|
| Python单元测试 | 206项运行通过，7项环境跳过；含180组视频/桌面/麦克风合并清单模拟 |
| Rust单元测试 | 现有测试二进制4/4通过；新增清单测试因本机离线缓存缺`windows`测试依赖未重建，正常debug/release源码编译均通过 |
| Python编译 | `python -m compileall -q .`通过 |
| 差异检查 | `git diff --check`通过，仅现有Windows CRLF提示 |
| 正式便携包 | `dist/MyAutoPlayer/MyAutoPlayer.exe`构建成功，3,063,825字节；SHA-256 `8431AF3026C895A946D38CFC8A6C0062DFA3EF240E371F08A3980AA5C8DADA5C` |
| 原生核心 | 725,504字节；源码release与包内SHA-256均为`5B2E0A39F8D46D8B2E562371D6F449E1D00CF1C965466CCF420E55725E15B1E2` |
| 打包模块 | PyInstaller xref包含`native_replay`、`input_subtitles`和`replay_history` |
| 发布隐私 | 正式包不含`replay_settings.json`、`key_monitor.json`、`ai_prompt.complete.md` |
| 残留进程 | `MyAutoPlayer`、原生录像核心、Cargo、Rustc均为0 |

发布构建不会复制本机录像保存路径、麦克风选择、窗口坐标或实时生成提示词。源码目录中的用户运行状态继续保留且被Git忽略。

两份可交付AI提示词`config/ai_prompt.md`与`config/ai_prompt.default.md`已核对为字节一致；完整第9节按键字典、动态第10/11节说明、录像事件字段、有限循环规则、双音轨与外挂字幕边界均为当前版本，本轮无需改写。

## 用户文件与已知边界

- 发布时以用户当前宏目录为准，保留顶层可运行脚本和`1-废弃脚本/`归档分组；不得恢复旧文件名、旧热键、旧循环次数或旧内容。`macros.zip`属于本地重复备份，不纳入源码仓库。
- 中文输入法下发送的物理字母仍会进入目标窗口IME组合态；用户已接受英文完全正确、中文轻微偶发现象。
- 不支持或禁止：鼠标轨迹、滚轮自动化、OCR/图像识别、游戏内存、DLL/驱动注入、OBS运行时依赖、手柄和反作弊绕过。
- GitHub发布继续排除`build/`、`dist/`、`captures/`、日志、优秀案例源码，以及`replay_settings.json`、`key_monitor.json`、`ai_prompt.complete.md`等本机私密运行状态。
