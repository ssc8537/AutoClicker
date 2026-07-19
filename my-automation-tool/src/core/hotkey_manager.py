"""全局单键和鼠标侧键触发管理；每个宏可独立并发运行。"""
from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes
from enum import IntEnum

import keyboard
from pynput import mouse


class TriggerMode(IntEnum):
    """DOWN 为按住，SWITCH 为按下一次启动、再按一次停止。"""

    SWITCH = 0
    DOWN = 1


MOUSE_HOTKEYS = frozenset({
    "mouse_left", "mouse_right", "mouse_middle", "mouse_back", "mouse_forward",
})


class HotkeyBinding:
    """一个宏的触发配置。相同热键允许有多个绑定。"""

    __slots__ = (
        "binding_id", "hotkey", "mode", "callback", "stop_callback",
        "stop_on_release", "is_running",
    )

    def __init__(
        self, binding_id: str, hotkey: str, mode: TriggerMode,
        callback, stop_callback=None, stop_on_release: bool = True,
    ):
        self.binding_id = binding_id
        self.hotkey = hotkey
        self.mode = mode
        self.callback = callback
        self.stop_callback = stop_callback
        self.stop_on_release = stop_on_release
        self.is_running = False


class HotkeyManager:
    """动态注册全局触发；重复热键会同时分发给所有启用宏。"""

    def __init__(self, main_window_hwnd: int = 0):
        self._bindings_by_id: dict[str, HotkeyBinding] = {}
        self._bindings_by_hotkey: dict[str, dict[str, HotkeyBinding]] = {}
        self._global_disabled = True
        self._global_disable_key: str | None = None
        self._global_disable_callback = None
        self._on_toggle_callbacks: list[callable] = []
        self._main_hwnd = main_window_hwnd
        self._hook_thread: threading.Thread | None = None
        self._mouse_listener: mouse.Listener | None = None
        self._lock = threading.RLock()
        self._pressed_hotkeys: set[str] = set()
        self._global_disable_key_pressed = False
        self._hooked_hotkeys: set[str] = set()
        self._listening = False

    def register(
        self, hotkey: str, callback, mode: TriggerMode = TriggerMode.DOWN,
        stop_callback=None, stop_on_release: bool = True, *, binding_id: str | None = None,
    ) -> str:
        """注册一个宏；相同 hotkey 不互相覆盖，返回绑定 ID。"""
        hotkey = hotkey.lower()
        binding_id = binding_id or hotkey
        self.unregister(binding_id)
        binding = HotkeyBinding(
            binding_id, hotkey, mode, callback, stop_callback, stop_on_release
        )
        with self._lock:
            self._bindings_by_id[binding_id] = binding
            self._bindings_by_hotkey.setdefault(hotkey, {})[binding_id] = binding
            hook_now = (
                self._listening
                and hotkey not in MOUSE_HOTKEYS
                and hotkey not in self._hooked_hotkeys
            )
        if hook_now:
            self._hook_key_once(hotkey)
        return binding_id

    def unregister(self, binding_id: str) -> bool:
        """注销一个宏绑定；若其正在执行，会先请求安全停止。"""
        stop_callback = None
        with self._lock:
            binding = self._bindings_by_id.pop(binding_id, None)
            if binding is None:
                return False
            bindings = self._bindings_by_hotkey.get(binding.hotkey)
            if bindings is not None:
                bindings.pop(binding_id, None)
                if not bindings:
                    self._bindings_by_hotkey.pop(binding.hotkey, None)
            if binding.is_running:
                binding.is_running = False
                stop_callback = binding.stop_callback
        if stop_callback is not None:
            stop_callback()
        return True

    def mark_finished(self, binding_id: str) -> None:
        """宏自然结束后释放该宏自己的触发状态。"""
        with self._lock:
            binding = self._bindings_by_id.get(binding_id)
            if binding is not None:
                binding.is_running = False

    def update_binding_configuration(
        self, binding_id: str, mode: TriggerMode, stop_on_release: bool
    ) -> bool:
        with self._lock:
            binding = self._bindings_by_id.get(binding_id)
            if binding is None:
                return False
            binding.mode = mode
            binding.stop_on_release = stop_on_release
            return True

    def start(self) -> None:
        if self._hook_thread is None or not self._hook_thread.is_alive():
            self._hook_thread = threading.Thread(
                target=self._listen_loop, daemon=True, name="hotkey-hook"
            )
            self._hook_thread.start()
        if self._mouse_listener is None:
            self._mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
            self._mouse_listener.start()

    def stop(self) -> None:
        keyboard.unhook_all()
        listener = self._mouse_listener
        self._mouse_listener = None
        if listener is not None:
            listener.stop()
            listener.join(timeout=1.0)
        if self._hook_thread:
            self._hook_thread.join(timeout=1.0)

    def set_global_disable_key(self, key: str) -> None:
        self._global_disable_key = key.lower()

    @property
    def global_disabled(self) -> bool:
        return self._global_disabled

    @global_disabled.setter
    def global_disabled(self, value: bool) -> None:
        self._global_disabled = value

    def toggle_global_disabled(self) -> bool:
        stop_callbacks = []
        with self._lock:
            self._global_disabled = not self._global_disabled
            disabled = self._global_disabled
            if disabled:
                for binding in self._bindings_by_id.values():
                    if binding.is_running:
                        binding.is_running = False
                        if binding.stop_callback:
                            stop_callbacks.append(binding.stop_callback)
            callbacks = list(self._on_toggle_callbacks)
        for callback in stop_callbacks:
            callback()
        for callback in callbacks:
            try:
                callback(disabled)
            except Exception:
                pass
        return disabled

    def on_toggle(self, callback: callable) -> None:
        self._on_toggle_callbacks.append(callback)

    def set_window_hwnd(self, hwnd: int) -> None:
        self._main_hwnd = hwnd

    def is_mouse_over_window(self) -> bool:
        if self._main_hwnd == 0:
            return False
        pt = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        rect = wintypes.RECT()
        if not ctypes.windll.user32.GetWindowRect(self._main_hwnd, ctypes.byref(rect)):
            return False
        return rect.left <= pt.x <= rect.right and rect.top <= pt.y <= rect.bottom

    def _listen_loop(self) -> None:
        with self._lock:
            self._listening = True
            hotkeys = [key for key in self._bindings_by_hotkey if key not in MOUSE_HOTKEYS]
            global_key = self._global_disable_key
        if global_key:
            keyboard.hook_key(global_key, self._on_global_disable_event)
        for hotkey in hotkeys:
            self._hook_key_once(hotkey)
        try:
            keyboard.wait()
        except Exception:
            pass

    def _hook_key_once(self, hotkey: str) -> None:
        with self._lock:
            if hotkey in self._hooked_hotkeys:
                return
            self._hooked_hotkeys.add(hotkey)
        keyboard.hook_key(hotkey, self._make_handler(hotkey))

    def _make_handler(self, hotkey: str):
        def handler(event):
            self._handle_event(hotkey, event.event_type == "down")
        return handler

    def _on_mouse_click(self, _x, _y, button, pressed) -> None:
        mapping = {
            mouse.Button.left: "mouse_left",
            mouse.Button.right: "mouse_right",
            mouse.Button.middle: "mouse_middle",
            getattr(mouse.Button, "x1", None): "mouse_back",
            getattr(mouse.Button, "x2", None): "mouse_forward",
        }
        hotkey = mapping.get(button)
        if hotkey is not None:
            self._handle_event(hotkey, pressed)


    def _handle_event(self, hotkey: str, is_pressed: bool) -> None:
        with self._lock:
            bindings = list(self._bindings_by_hotkey.get(hotkey, {}).values())
            if not bindings:
                return
            if is_pressed:
                if hotkey in self._pressed_hotkeys:
                    return
                self._pressed_hotkeys.add(hotkey)
            else:
                if hotkey not in self._pressed_hotkeys:
                    return
                self._pressed_hotkeys.remove(hotkey)
            disabled = self._global_disabled
        if is_pressed and (disabled or self.is_mouse_over_window()):
            return
        callbacks = []
        stop_callbacks = []
        with self._lock:
            for binding in bindings:
                if self._bindings_by_id.get(binding.binding_id) is not binding:
                    continue
                if binding.mode == TriggerMode.SWITCH:
                    if not is_pressed:
                        continue
                    if binding.is_running:
                        binding.is_running = False
                        if binding.stop_callback:
                            stop_callbacks.append(binding.stop_callback)
                    else:
                        binding.is_running = True
                        callbacks.append(binding.callback)
                elif is_pressed:
                    if not binding.is_running:
                        binding.is_running = True
                        callbacks.append(binding.callback)
                elif binding.is_running and binding.stop_on_release:
                    binding.is_running = False
                    if binding.stop_callback:
                        stop_callbacks.append(binding.stop_callback)
        for callback in callbacks:
            callback()
        for callback in stop_callbacks:
            callback()

    def _on_global_disable_event(self, event) -> None:
        if event.event_type == "up":
            with self._lock:
                self._global_disable_key_pressed = False
            return
        if event.event_type != "down":
            return
        with self._lock:
            if self._global_disable_key_pressed:
                return
            self._global_disable_key_pressed = True
        self.toggle_global_disabled()
