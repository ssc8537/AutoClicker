# 项目知识文档 — 从优秀案例深度提取的设计模式与代码骨架

本文档记录了从两个参考项目中提炼的、对本项目有直接启发价值的设计思路和代码模式。
每次开发前，Codex 必须阅读本文档。

---

## 一、输入模拟实现（深度参考 ok-ww）

### 1.1 接口设计（从 BaseWWTask.click() 和 send_key 调用提取）

ok-ww 的按键模拟调用链：角色脚本 → BaseChar → self.task.send_key() → BaseWWTask → super().send_key() → ok 框架底层

**实际使用的接口签名**（从 BaseWWTask 源码提取）：

```python
# 按键操作 - 从 BaseWWTask 多处调用提取
self.send_key(key, after_sleep=0.01)
    # key: str - 按键字符，如 "1", "e", "esc", "f2"
    # after_sleep: float - 发送后等待秒数

self.send_key_down(key)
    # 按下并保持（用于 WASD 移动、蓄力等）

self.send_key_up(key)
    # 释放按键

# 鼠标操作 - 从 BaseWWTask.click() 方法签名提取
self.click(x=-1, y=-1, move_back=False, name=None, interval=-1, move=False,
           down_time=0.01, after_sleep=0, key="left")
    # x, y: 屏幕坐标，-1 表示屏幕中心
    # down_time: 按下持续时间，普攻类操作 0.01s，交互类 0.2s
    # after_sleep: 操作后等待
    # key: "left" / "right"

self.mouse_down(key="right")
    # 按下鼠标键（用于跑步等持续操作）

self.mouse_up(key="right")
    # 释放鼠标键
```

### 1.2 本项目 input_simulator.py 的推荐实现骨架

核心使用 ctypes 调用 Windows SendInput API，保证游戏兼容性。虚拟键码映射表覆盖常用按键（0-9, a-z, F1-F12, space, enter, esc, 方向键）。

```python
def tap_key(key: str, duration: float = 0.05) -> None:
    vk = _VK_MAP.get(key.lower())
    if vk is None: raise ValueError(f"未知按键: {key}")
    _send_input(_make_kb_input(vk))
    time.sleep(duration)
    _send_input(_make_kb_input(vk, KEYEVENTF_KEYUP))

def press_key(key: str) -> None: ...
def release_key(key: str) -> None: ...
def click_mouse(button: str = "left") -> None: ...
def mouse_down(button: str = "left") -> None: ...
def mouse_up(button: str = "left") -> None: ...
```

**关键经验**（从 ok-ww 学到）：
- 游戏需要精确的按键持续时间（down_time），太短可能不被识别
- 每个操作之间默认插入约 10ms 间隔，保证游戏正确接收连续输入
- pynput 在某些游戏被反作弊屏蔽，SendInput 更可靠

---

## 二、热键绑定与三种触发模式（深度参考 Quickinput trigger.cpp）

### 2.1 触发模式枚举

Quickinput 的 `macro.h` 定义了枚举 `enum TriggerMode { sw, down, up }`。

对应本项目：
```python
from enum import IntEnum

class TriggerMode(IntEnum):
    SWITCH = 0   # 切换：第一次按下开始循环，再次按下停止
    DOWN = 1     # 按住：按住热键期间持续执行，松开停止
    UP = 2       # 松开：松开热键时执行一轮
```

### 2.2 状态机逻辑（从 trigger.cpp switch/case 提取）

Quickinput 的 `trigger.cpp` 通过 `switch(macro.mode)` 分发三种模式。

**本项目 hotkey_manager.py 的实现骨架**：

```python
"""热键管理器 - 全局热键注册、焦点检测、触发模式分发"""
import keyboard
from threading import Event
from enum import IntEnum

class HotkeyBinding:
    def __init__(self, script_name, hotkey, mode, callback, stop_callback):
        self.script_name = script_name
        self.hotkey = hotkey
        self.mode = mode
        self.callback = callback      # 启动脚本回调
        self.stop_callback = stop_callback  # 停止脚本回调
        self.is_running = False


class HotkeyManager:
    def __init__(self, main_window_hwnd):
        self._bindings = {}
        self._global_disabled = False
        self._main_hwnd = main_window_hwnd

    def _on_key_event(self, key: str, is_pressed: bool):
        if self._global_disabled:
            return
        if self._is_mouse_over_window():
            return  # 鼠标在窗口内，抑制触发

        binding = self._bindings.get(key)
        if not binding: return

        # 三种触发模式的分发逻辑（从 Quickinput trigger.cpp 提取）
        if binding.mode == TriggerMode.SWITCH:
            if is_pressed:
                if binding.is_running:
                    binding.stop_callback()
                    binding.is_running = False
                else:
                    binding.callback()
                    binding.is_running = True
        elif binding.mode == TriggerMode.DOWN:
            if is_pressed:
                binding.callback()
                binding.is_running = True
            else:
                binding.stop_callback()
                binding.is_running = False
        elif binding.mode == TriggerMode.UP:
            if not is_pressed:
                binding.callback()

    def _is_mouse_over_window(self) -> bool:
        """检测鼠标是否在程序窗口内"""
        import ctypes
        from ctypes import wintypes
        pt = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(self._main_hwnd, ctypes.byref(rect))
        return rect.left <= pt.x <= rect.right and rect.top <= pt.y <= rect.bottom
```

---

## 三、线程管理模型（深度参考 Quickinput thread.h）

### 3.1 QiThreadManager 核心设计

Quickinput 的 `thread.h` 实现了一个**可中断的 detached-thread 管理器**：

```cpp
struct QiWorker {
    std::atomic_bool m_stop;  // 原子停止标志

    void sleep(clock_t ms) {
        // 可中断的 sleep：每 1ms 检查 m_stop，为 true 则立即返回
        while (!m_stop && clock() < end)
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    virtual void run() = 0;
};
```

**关键洞察**：
- 使用 `std::atomic_bool` 作为停止标志——线程安全且无需锁
- 不使用 `.join()`，而是 `.detach()`——线程自行结束
- sleep 不是 `time.sleep()`，而是可中断的忙等待——保证停止响应 < 1ms

### 3.2 本项目 sequence_player.py 的线程模型

```python
"""序列播放器 - 在线程中执行按键序列，支持即时中断"""
import time
import threading

class SequencePlayer:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None

    def play(self, sequence: list, speed_factor: float = 1.0):
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._execute, args=(sequence, speed_factor), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _execute(self, sequence: list, speed_factor: float):
        for action_type, value, delay_ms in sequence:
            if self._stop_event.is_set():
                return  # 立即退出
            self._perform_action(action_type, value)
            # 可中断的 sleep（仿 Quickinput QiWorker::sleep）
            adjusted_delay = delay_ms * speed_factor / 1000.0
            deadline = time.time() + adjusted_delay
            while time.time() < deadline:
                if self._stop_event.is_set():
                    return
                time.sleep(0.001)  # 1ms 粒度检查
```

---

## 四、窗口匹配与焦点检测（深度参考 Quickinput macro.h WndMatch）

### 4.1 Quickinput 的 WndMatch 结构

Quickinput 的焦点检测逻辑（`macro.h`）：

```cpp
struct WndMatch {
    HWND wnd = nullptr;
    QString name;   // 窗口标题（支持通配符）
    QString clas;   // 窗口类名
    QString proc;   // 进程路径

    void update(HWND hwnd = nullptr) {
        wnd = hwnd ? hwnd : GetForegroundWindow();
        name = Window::text(wnd);
        clas = Window::className(wnd);
        GetWindowThreadProcessId(wnd, &pid);
        proc = Process::path(pid);
    }
};
```

**本项目方案**：用户需求是"鼠标不在程序窗口内才触发"，只需检测鼠标位置 vs 窗口矩形（见第二章 `_is_mouse_over_window` 实现）。如果将来需要扩展为"仅在特定游戏窗口激活时触发"，可以借鉴 WndMatch 的通配符匹配逻辑。

---

## 五、模块化架构与类继承（深度参考 ok-ww BaseChar）

### 5.1 BaseChar 的基类设计

ok-ww 的 `BaseChar.py` 展示了一个清晰的基类模式：

- **每个角色一个独立文件**，继承 BaseChar
- BaseChar 提供通用方法：`click_resonance()`, `click_liberation()`, `click_echo()`, `heavy_attack()`, `switch_next_char()`
- 子类重写 `do_perform()` 实现具体连招逻辑
- `self.task` 引用提供底层 API：`send_key()`, `click()`, `sleep()`, `next_frame()`

### 5.2 对本项目的启示——ScriptPlayer API

```python
# 提供给用户的 player API（仿 ok-ww task 接口）
class ScriptPlayer:
    def press(self, key: str):
        """按下并释放按键 - 对应 task.send_key()"""
    def sleep(self, ms: float):
        """等待毫秒 - 对应 BaseChar.sleep()"""
    def click(self, button="left"):
        """鼠标点击 - 对应 task.click()"""
    def hold(self, key: str, duration: float):
        """按住按键一段时间 - 对应 send_key_down/send_key_up"""
```

---

## 六、可复用代码清单

| 来源 | 代码位置 | 复用内容 |
|------|----------|----------|
| ok-ww BaseWWTask | click(), send_key() | 接口参数设计（down_time, after_sleep） |
| ok-ww BaseWWTask | send_key_down/up | WASD 移动/蓄力的按键保持模式 |
| Quickinput trigger.cpp | switch(macro.mode) | 三种触发模式的完整分发逻辑 |
| Quickinput thread.h | QiThreadManager | detached-thread + atomic_bool 模型 |
| Quickinput thread.h | QiWorker::sleep | 可中断 sleep（1ms 粒度 + 停止标志） |
| Quickinput macro.h | WndMatch::update | 前台窗口信息获取 |
| ok-ww BaseChar | __init__ + Logger | 子类化 + self.task + 日志模式 |

---

## 七、避坑指南

1. **pynput vs SendInput**：pynput 在某些游戏被反作弊屏蔽。ok-ww 经验是直接用 ctypes 调用 SendInput。本项目应首选 SendInput。

2. **热键冲突**：多个脚本绑定同一热键时必须有确定的行为（警告/禁止）。全局禁用键不能被任何脚本占用。

3. **线程安全**：键盘监听在后台线程，PySide6 UI 操作必须在主线程——使用 Signal/Slot 通信。

4. **管理员权限**：部分游戏需要管理员权限才能 SendInput。程序应检测并在需要时提示。

5. **sleep 的粒度**：不要用 `time.sleep(0.01)` 做循环等待——它不可中断。使用带 `threading.Event` 检查的短 sleep。Quickinput 的 QiWorker::sleep 用 1ms 粒度 + atomic_bool 检查——本项目中直接采用。

6. **detached thread 生命周期**：Python daemon thread 等效 detached thread。必须在主程序退出前设置 stop_event，否则线程可能访问已销毁对象。
