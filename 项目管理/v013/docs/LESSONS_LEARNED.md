# 经验教训：自动化按键项目的进程管理

> 本文档记录了一次真实事故的复盘：删除了运行中的 Python 自动化脚本源代码，导致孤儿进程在后台持续运行十几个小时，鼠标侧键和小键盘 0 键不受控制地触发自动按键序列。这份经验可以被另一个 AI 自动化项目直接引用，避免同类问题。

---

## 一、事故经过

1. 你开发了一个 `GameMacroManager.pyw`（游戏连招宏管理工具），使用 Python + tkinter + Win32 API 实现全局热键轮询，绑定 **XButton1（鼠标前侧键）**、**XButton2（鼠标后侧键）**、**Numpad0（小键盘 0）** 触发自动按键序列。
2. 在程序**仍在后台运行**的情况下，你删除了源代码文件。
3. 数月后复原代码，发现按下上述按键仍然触发自动操作，但找不到地方关闭。
4. 排查发现：4 个 `pythonw.exe` 孤儿进程（来自另一个已删除的 `QiAutoClicker.pyw`）在后台存活了 12+ 小时，持续执行全局按键监听。

---

## 二、根因分析

### 2.1 Python 进程的生命周期特性

- `pythonw.exe`（而不是 `python.exe`）不会显示控制台窗口，用户完全感知不到它在后台运行。
- 即使源代码文件被删除，Python 进程不会因此退出。解释器已将代码加载到内存中，`.pyc` 缓存文件可以继续提供字节码。
- `Get-Process` 看到的进程命令行仍指向原文件路径，即使原文件已不存在。

### 2.2 用户感知断层

- GUI 窗口被关闭 != 进程退出（如果程序使用 `pythonw.exe` 启动且后台线程未退出）。
- 没有系统托盘图标或通知，用户无法直观判断程序是否还在运行。
- `macros.json` 配置文件为空（`[]`），说明用户删除代码前未保存配置，但也反映了配置持久化的薄弱环节。

---

## 三、诊断与解决方法（Windows PowerShell）

```powershell
# 1. 查看所有 python 相关进程
Get-Process | Where-Object { $_.ProcessName -like '*python*' }

# 2. 查看进程的完整命令行（确定每个进程的来源）
Get-WmiObject Win32_Process | Where-Object { $_.Name -match 'python' } |
    Select-Object ProcessId, Name, CommandLine

# 3. 查看进程启动时间（判断是否异常存活）
Get-Process pythonw | Select-Object Id, StartTime, CPU

# 4. 杀掉所有 pythonw 进程（解决孤儿进程问题）
Get-Process -Name pythonw | Stop-Process -Force

# 5. 验证是否清理干净
Get-Process -Name pythonw -ErrorAction SilentlyContinue
```

> `Get-Process -Name pythonw | Stop-Process -Force` 是最直接、最有效的解法，一条命令解决所有弃用进程。

---

## 四、给自动化项目开发的架构建议

### 4.1 进程可视化管理

| 机制 | 说明 |
|------|------|
| 系统托盘图标 | 使用 `pystray` 或 Win32 API 在系统托盘常驻图标，右键可关闭/重启/查看状态 |
| 进程信号文件 | 启动时创建一个 `.lock` 或 `.pid` 文件，退出时删除。用户或另一个程序可通过检查该文件判断是否在运行 |
| 任务管理器可见 | 避免使用 `pythonw.exe` 启动关键工具，或用自定义进程名（如 `--process-name`）让用户能识别 |

### 4.2 热键开关设计

GameMacroManager 的设计是正确的方向，但可以做得更好：

- **全局开关必须醒目**：工具栏的 "Global: ON/OFF" 按钮是核心控件，建议使用颜色区分（绿色=开启，红色=关闭）而不是纯文字。
- **热键切换**：提供一个硬编码的紧急停止热键（如 `Ctrl+Alt+F12`），任何时候按下都能强制停止所有热键轮询。
- **窗口关闭 = 完全退出**：`WM_DELETE_WINDOW` 事件处理中，确保先停止所有工作线程，再销毁窗口，最后退出进程。当前代码已经做到了这一点：
  ```python
  def on_close(self):
      Config.save()        # 保存配置
      HotkeyPoller.enabled = False  # 停止热键轮询
      self.root.destroy()  # 销毁窗口
  ```

### 4.3 进程防孤儿策略

- **atexit 注册清理函数**：在 Python 中注册 `atexit.register(cleanup)` 确保进程退出时释放全局钩子。
- **看门狗机制**：主线程监控子线程心跳，如果 GUI 线程意外退出，子线程自动退出。
- **互斥锁 / 唯一实例**：使用 `win32event.CreateMutex` 确保同一程序只有一个实例运行，新实例启动时杀死旧实例。

### 4.4 配置与数据持久化

- **自动保存**：修改宏配置后，设置 3 秒防抖自动保存到 `macros.json`，而不是等到窗口关闭才保存。
- **备份机制**：保存前先备份旧文件（`macros.json.bak`），防止写坏。
- **配置校验**：加载时验证 JSON 结构完整性，损坏时自动从备份恢复。

### 4.5 调试与排障能力

- **日志系统**：将程序运行日志写入 `logs/` 目录（包含启动时间、热键注册状态、异常信息）。
- **健康检查 API**：运行一个本地 HTTP 接口（如 `http://127.0.0.1:18732/status`），返回 JSON 格式的运行状态。
- **进程列表导出**：提供导出当前运行配置和进程信息的功能，方便排查。

---

## 五、Windows 平台排查速查表

| 命令 | 用途 |
|------|------|
| `Get-Process -Name pythonw` | 查看所有后台 Python 进程 |
| `Get-WmiObject Win32_Process \| Where-Object { $_.Name -match 'python' }` | 查看进程的完整命令行 |
| `Get-Process \| Where-Object { $_.ProcessName -like '*AutoHotkey*' }` | 查看 AutoHotkey 进程 |
| `Get-ScheduledTask \| Where-Object { ... }` | 检查任务计划程序中的自动化任务 |
| `Get-CimInstance Win32_StartupCommand` | 查看开机自启项 |
| `tasklist /M *hook*` | 查看加载了全局钩子的进程 |
| `Get-Process -Name pythonw \| Stop-Process -Force` | 紧急停止所有 Python 后台进程 |

---

## 六、关键原则总结

1. **删除不先关 = 鬼进程** — 删除运行中的 Python 脚本前，一定要先通过 GUI 正常退出或 `Stop-Process` 杀掉进程。
2. **用户看不到 != 程序没在跑** — `pythonw.exe` 后台进程没有任何窗口，只能通过任务管理器或命令行发现。
3. **GUI 需要双向可见性** — 不仅有控制入口，还要有状态指示（系统托盘、颜色标签、日志）。
4. **紧急停止不能依赖 GUI** — 如果 GUI 被关闭但进程存活，需要独立的紧急停止机制（特定热键或命令行命令）。
5. **AI 项目之间的经验传递** — 这个文档可以直接交给另一个 AI，让它理解这个项目的上下文、架构优缺点和工程陷阱，无需额外解释。

---

## 七、Qt 全局热键线程经验（审查 #12）

### 问题与根因
`keyboard` 的全局热键回调运行在后台钩子线程。直接在回调中调用 Qt 控件、显示 OSD 或执行依赖 GUI 线程状态的逻辑，会造成跨线程访问风险；连续按 F9 还可能让多次执行重叠。

### 固定防范方式
钩子线程只能调用 `_HotkeyDispatcher.on_f9_hook` / `on_toggle_hook` 并发射 Qt 信号。Qt 主线程槽函数负责输入、OSD 和状态标签更新；F9 使用非阻塞 `threading.Lock`，未取得锁的连按直接丢弃，并在成功、异常和信号转发失败路径释放锁。

### 编码记录
`SETUP_GUIDE.md` 必须保留 UTF-8 BOM（`EF BB BF`），以便中文 Windows PowerShell 自动正确识别中文编码；更新文件后必须检查前三个字节。

---

## 八、热键重复事件与产品语义必须分开（审查 #13）

### 问题
阶段 1 的 `PRESS` 热键在按住 F9 时接收重复按下事件，导致 Hello World 在一次长按内反复执行。非阻塞锁只能避免重叠，不能把一次物理长按识别为一次触发。

### 防范原则
先明确产品语义，再选择实现：单次执行必须做“物理按下去重，释放后才允许下一次”；按住执行必须显式监听按下和释放，使用可取消的执行循环，并在释放时通知停止。不能将重复事件误当作已经实现的按住模式。
