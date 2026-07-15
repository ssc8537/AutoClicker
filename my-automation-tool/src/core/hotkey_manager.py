"""热键管理器 — 全局热键注册、焦点检测、触发模式分发。

参考：Quickinput trigger.cpp 的 switch/case 三种触发模式状态机。
底层使用 keyboard 库实现全局钩子。

用法：
    from src.core.hotkey_manager import HotkeyManager
    mgr = HotkeyManager(main_window_hwnd)
    mgr.register("f9", callback)  # 注册 F9 热键
    mgr.start()
"""
import ctypes
import threading
from ctypes import wintypes
from enum import IntEnum

import keyboard


class TriggerMode(IntEnum):
    """触发模式（参考 Quickinput macro.h enum TriggerMode）。

    SWITCH — 切换：按下启动/停止切换
    DOWN   — 按住：按住热键持续执行，松开停止
    UP     — 松开：松开热键时执行一轮
    PRESS  — 按下执行一轮（阶段 1 Hello World 默认模式）
    """
    SWITCH = 0
    DOWN = 1
    UP = 2
    PRESS = 3


class HotkeyBinding:
    """单个热键绑定。"""

    __slots__ = ("hotkey", "mode", "callback", "stop_callback", "is_running")

    def __init__(self, hotkey: str, mode: TriggerMode,
                 callback, stop_callback=None):
        self.hotkey = hotkey
        self.mode = mode
        self.callback = callback
        self.stop_callback = stop_callback
        self.is_running = False


class HotkeyManager:
    """全局热键管理器。

    核心行为（参考 Quickinput trigger.cpp）：
    - 全局禁用状态下所有热键失效
    - 鼠标在程序窗口内时抑制触发
    - 三种触发模式：SWITCH / DOWN / UP / PRESS
    """

    def __init__(self, main_window_hwnd: int = 0):
        self._bindings: dict[str, HotkeyBinding] = {}
        self._global_disabled = True  # 安全机制：启动即禁用
        self._global_disable_key: str | None = None
        self._global_disable_callback = None
        self._on_toggle_callbacks: list[callable] = []
        self._main_hwnd = main_window_hwnd
        self._hook_thread: threading.Thread | None = None
        self._lock = threading.Lock()

    # ── 注册 / 注销 ──────────────────────────────────────────────────

    def register(self, hotkey: str, callback,
                 mode: TriggerMode = TriggerMode.PRESS,
                 stop_callback=None) -> None:
        """注册一个热键绑定。

        Args:
            hotkey: keyboard 库识别的键名（如 "f9", "ctrl+shift+a"）
            callback: 热键触发时的回调（无参数）
            mode: 触发模式
            stop_callback: 停止回调（SWITCH 和 DOWN 模式需要）
        """
        with self._lock:
            self._bindings[hotkey] = HotkeyBinding(
                hotkey, mode, callback, stop_callback
            )

    def unregister(self, hotkey: str) -> bool:
        """注销一个热键绑定。返回是否成功。"""
        with self._lock:
            return self._bindings.pop(hotkey, None) is not None

    # ── 生命周期 ─────────────────────────────────────────────────────

    def start(self) -> None:
        """启动后台键盘监听线程。"""
        if self._hook_thread is not None and self._hook_thread.is_alive():
            return
        self._hook_thread = threading.Thread(
            target=self._listen_loop, daemon=True, name="hotkey-hook"
        )
        self._hook_thread.start()

    def stop(self) -> None:
        """停止后台监听。"""
        # keyboard 库通过 unhook 清理，线程会在 unhook_all 后自然退出
        keyboard.unhook_all()
        if self._hook_thread:
            self._hook_thread.join(timeout=1.0)

    # ── 全局禁用 ─────────────────────────────────────────────────────

    def set_global_disable_key(self, key: str) -> None:
        """设置全局禁用热键。"""
        self._global_disable_key = key

    @property
    def global_disabled(self) -> bool:
        return self._global_disabled

    @global_disabled.setter
    def global_disabled(self, value: bool) -> None:
        self._global_disabled = value

    def toggle_global_disabled(self) -> bool:
        """切换全局禁用状态。返回新状态。"""
        self._global_disabled = not self._global_disabled
        for cb in self._on_toggle_callbacks:
            try:
                cb(self._global_disabled)
            except Exception:
                pass
        return self._global_disabled

    def on_toggle(self, callback: callable) -> None:
        """注册全局禁用状态切换时的通知回调。
        
        Args:
            callback: 接收一个 bool 参数（True=禁用, False=启用）
        """
        self._on_toggle_callbacks.append(callback)

    # ── 焦点检测 ─────────────────────────────────────────────────────

    def set_window_hwnd(self, hwnd: int) -> None:
        """更新主窗口句柄（窗口创建后调用）。"""
        self._main_hwnd = hwnd

    def is_mouse_over_window(self) -> bool:
        """检测鼠标是否在程序窗口内。

        使用 Win32 API：GetCursorPos + GetWindowRect。
        窗口最小化时 GetWindowRect 可能返回不可靠值，但根据已确认决策，
        最小化时照常允许热键触发（此处不检测最小化状态）。
        """
        if self._main_hwnd == 0:
            return False
        pt = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        rect = wintypes.RECT()
        if not ctypes.windll.user32.GetWindowRect(self._main_hwnd, ctypes.byref(rect)):
            return False  # 获取窗口矩形失败，保守返回 False（不抑制）
        return rect.left <= pt.x <= rect.right and rect.top <= pt.y <= rect.bottom

    # ── 内部 ─────────────────────────────────────────────────────────

    def _listen_loop(self) -> None:
        """后台键盘监听循环。"""
        # 注册全局禁用键切换
        if self._global_disable_key:
            keyboard.add_hotkey(
                self._global_disable_key, self._on_global_disable
            )
        # 为所有绑定注册钩子
        for hotkey in self._bindings:
            keyboard.add_hotkey(hotkey, self._make_handler(hotkey))
        # 阻塞等待（keyboard 库内部事件循环）
        try:
            keyboard.wait()
        except Exception:
            pass

    def _make_handler(self, hotkey: str):
        """为每个热键创建闭包处理函数。"""

        def handler():
            with self._lock:
                binding = self._bindings.get(hotkey)
                if binding is None:
                    return

            if self._global_disabled:
                return
            if self.is_mouse_over_window():
                return  # 鼠标在窗口内，抑制触发

            mode = binding.mode
            if mode == TriggerMode.PRESS:
                binding.callback()
            elif mode == TriggerMode.SWITCH:
                with self._lock:
                    if binding.is_running:
                        if binding.stop_callback:
                            binding.stop_callback()
                        binding.is_running = False
                    else:
                        binding.callback()
                        binding.is_running = True
            elif mode == TriggerMode.DOWN:
                binding.callback()
                with self._lock:
                    binding.is_running = True
            elif mode == TriggerMode.UP:
                # UP 模式通过 hook_key 的 press/release 事件实现
                # 简单实现：用键盘钩子监听释放事件
                pass

        return handler

    def _on_global_disable(self) -> None:
        """全局禁用键回调。"""
        self.toggle_global_disabled()
