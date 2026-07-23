"""全局单键和鼠标侧键触发管理；每个宏可独立并发运行。"""
from __future__ import annotations

import ctypes
import os
import queue
import threading
import time
from dataclasses import dataclass
from ctypes import wintypes
from enum import IntEnum

from pynput import keyboard, mouse

from src.core.input_keys import MOUSE_HOTKEYS, input_key_from_windows_vk, normalise_input_key
from src.core.input_simulator import INPUT_EVENT_MARKER
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class PhysicalInputEvent:
    hotkey: str
    pressed: bool
    vk: int | None
    monotonic_ns: int
    foreground_hwnd: int
    foreground_pid: int


class TriggerMode(IntEnum):
    """DOWN 为按住，SWITCH 为按下一次启动、再按一次停止。"""

    SWITCH = 0
    DOWN = 1


class HotkeyBinding:
    """一个宏的触发配置。相同热键允许有多个绑定。"""

    __slots__ = (
        "binding_id", "hotkey", "mode", "callback", "stop_callback",
        "stop_on_release", "is_running", "generation",
    )

    def __init__(
        self, binding_id: str, hotkey: str, mode: TriggerMode,
        callback, stop_callback=None, stop_on_release: bool = True,
        generation: int = 0,
    ):
        self.binding_id = binding_id
        self.hotkey = hotkey
        self.mode = mode
        self.callback = callback
        self.stop_callback = stop_callback
        self.stop_on_release = stop_on_release
        self.is_running = False
        self.generation = generation


class HotkeyManager:
    """动态注册全局触发；重复热键会同时分发给所有启用宏。"""

    def __init__(self, main_window_hwnd: int = 0):
        self._bindings_by_id: dict[str, HotkeyBinding] = {}
        self._bindings_by_hotkey: dict[str, dict[str, HotkeyBinding]] = {}
        # binding 被禁用、改键或重建后也不能把代次重置为 0。调度器会用代次
        # 拒绝“松开后才到达”的旧启动；代次倒退会把新启动误判成旧事件。
        self._generation_floor_by_id: dict[str, int] = {}
        # 用户要求每次启动即可使用宏触发键；启动不会自动执行任何宏，
        # 只有后续真实按下某个已启用宏的绑定键才会运行。
        self._global_disabled = False
        self._global_disable_key: str | None = None
        self._global_disable_callback = None
        self._on_toggle_callbacks: list[callable] = []
        self._main_hwnd = main_window_hwnd
        self._keyboard_listener: keyboard.Listener | None = None
        self._mouse_listener: mouse.Listener | None = None
        self._event_thread: threading.Thread | None = None
        self._event_queue: queue.Queue[tuple[str, bool, int] | None] = queue.Queue(maxsize=512)
        self._queue_overflow_logged = False
        self._config_epoch = 0
        self._lock = threading.RLock()
        self._pressed_hotkeys: set[str] = set()
        self._queued_physical_state: dict[str, bool] = {}
        self._global_disable_key_pressed = False
        self._trigger_suppressed = False
        self._listening = False
        self._physical_observers: list[callable] = []

    def set_trigger_suppressed(self, suppressed: bool) -> None:
        """Temporarily block new macro/global-toggle presses without hiding observers.

        The replay/key-monitor observers still receive the original physical edges. Releases
        are also allowed through so an already running down-mode macro can stop safely.
        """
        with self._lock:
            self._trigger_suppressed = bool(suppressed)

    def add_physical_observer(self, callback) -> None:
        with self._lock:
            if callback not in self._physical_observers:
                self._physical_observers.append(callback)

    def remove_physical_observer(self, callback) -> None:
        with self._lock:
            if callback in self._physical_observers:
                self._physical_observers.remove(callback)

    def _notify_physical_observers(
        self, hotkey: str, pressed: bool, vk: int | None
    ) -> None:
        with self._lock:
            observers = tuple(self._physical_observers)
        if not observers:
            return
        hwnd = int(ctypes.windll.user32.GetForegroundWindow() or 0)
        pid = wintypes.DWORD()
        if hwnd:
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        event = PhysicalInputEvent(
            hotkey,
            pressed,
            vk,
            time.perf_counter_ns(),
            hwnd,
            int(pid.value),
        )
        for observer in observers:
            try:
                observer(event)
            except Exception:
                logger.exception("物理输入观察器异常，已隔离")

    def register(
        self, hotkey: str, callback, mode: TriggerMode = TriggerMode.DOWN,
        stop_callback=None, stop_on_release: bool = True, *, binding_id: str | None = None,
    ) -> str:
        """注册一个宏；相同 hotkey 不互相覆盖，返回绑定 ID。"""
        hotkey = normalise_input_key(hotkey)
        binding_id = binding_id or hotkey
        self.unregister(binding_id)
        with self._lock:
            binding = HotkeyBinding(
                binding_id,
                hotkey,
                mode,
                callback,
                stop_callback,
                stop_on_release,
                self._generation_floor_by_id.get(binding_id, 0),
            )
            self._bindings_by_id[binding_id] = binding
            self._bindings_by_hotkey.setdefault(hotkey, {})[binding_id] = binding
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
                generation = self._advance_generation_locked(binding)
                stop_callback = binding.stop_callback
            else:
                generation = binding.generation
                self._generation_floor_by_id[binding_id] = max(
                    generation, self._generation_floor_by_id.get(binding_id, 0)
                )
        if stop_callback is not None:
            stop_callback(generation)
        return True

    def mark_finished(self, binding_id: str, generation: int | None = None) -> None:
        """只允许完成回调结束自己那一代运行，旧回调不得覆盖新运行。"""
        with self._lock:
            binding = self._bindings_by_id.get(binding_id)
            if binding is not None and (
                generation is None or binding.generation == generation
            ):
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

    def _advance_generation_locked(self, binding: HotkeyBinding) -> int:
        """锁内递增并保存绑定代次；跨注销/重新启用保持单调。"""
        binding.generation += 1
        self._generation_floor_by_id[binding.binding_id] = max(
            binding.generation,
            self._generation_floor_by_id.get(binding.binding_id, 0),
        )
        return binding.generation

    def clear_pending_events(self) -> int:
        """配置即时刷新时丢弃旧边沿与按住状态，避免历史队列延迟新绑定。"""
        with self._lock:
            self._pressed_hotkeys.clear()
            self._queued_physical_state.clear()
            self._global_disable_key_pressed = False
            self._queue_overflow_logged = False
            self._config_epoch += 1
        removed = 0
        while True:
            try:
                event = self._event_queue.get_nowait()
            except queue.Empty:
                break
            if event is None:
                self._event_queue.put_nowait(None)
                break
            removed += 1
        return removed

    def start(self) -> None:
        with self._lock:
            if self._listening:
                return
            self._listening = True
        self._event_thread = threading.Thread(
            target=self._event_loop, daemon=True, name="hotkey-events"
        )
        self._event_thread.start()
        self._keyboard_listener = keyboard.Listener(
            # Windows 必须走原始 KBDLLHOOKSTRUCT.vkCode。若先由 pynput
            # 翻译为字符，中文 IME 会把物理键变成 PROCESSKEY/输入法字符。
            on_press=lambda *_args: None,
            on_release=lambda *_args: None,
            win32_event_filter=self._on_windows_keyboard_event,
        )
        self._keyboard_listener.start()
        self._keyboard_listener.wait()
        if self._mouse_listener is None:
            # 和键盘一样直接读取 Windows 低级 hook 数据；不依赖高层按钮翻译，
            # 只过滤本程序自己的 dwExtraInfo 标记。
            self._mouse_listener = mouse.Listener(
                on_click=lambda *_args: None,
                win32_event_filter=self._on_windows_mouse_event,
            )
            self._mouse_listener.start()
            self._mouse_listener.wait()

    def stop(self) -> None:
        with self._lock:
            self._listening = False
            self._pressed_hotkeys.clear()
            self._queued_physical_state.clear()
            self._global_disable_key_pressed = False
        keyboard_listener = self._keyboard_listener
        self._keyboard_listener = None
        if keyboard_listener is not None:
            keyboard_listener.stop()
            keyboard_listener.join(timeout=1.0)
        listener = self._mouse_listener
        self._mouse_listener = None
        if listener is not None:
            listener.stop()
            listener.join(timeout=1.0)
        self._event_queue.put(None)
        if self._event_thread:
            self._event_thread.join(timeout=1.0)
        self._event_thread = None

    def set_global_disable_key(self, key: str) -> None:
        canonical = normalise_input_key(key)
        with self._lock:
            self._global_disable_key = canonical
            self._global_disable_key_pressed = False

    @property
    def global_disable_key(self) -> str | None:
        return self._global_disable_key

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
                        generation = self._advance_generation_locked(binding)
                        if binding.stop_callback:
                            stop_callbacks.append((binding.stop_callback, generation))
            callbacks = list(self._on_toggle_callbacks)
        for callback, generation in stop_callbacks:
            callback(generation)
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
        # 仅当本程序确实处于前台时，才抑制窗口区域内的鼠标触发。
        # 游戏覆盖窗口后仍会保留旧窗口矩形，且常把鼠标锁在屏幕中央；
        # 若只看坐标，会把游戏中的真实侧键按下静默丢弃。
        foreground = ctypes.windll.user32.GetForegroundWindow()
        if not foreground:
            return False
        foreground_pid = wintypes.DWORD()
        if not ctypes.windll.user32.GetWindowThreadProcessId(
            foreground, ctypes.byref(foreground_pid)
        ):
            return False
        if foreground_pid.value != os.getpid():
            return False
        pt = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        rect = wintypes.RECT()
        if not ctypes.windll.user32.GetWindowRect(self._main_hwnd, ctypes.byref(rect)):
            return False
        return rect.left <= pt.x <= rect.right and rect.top <= pt.y <= rect.bottom

    def _make_handler(self, hotkey: str):
        def handler(event):
            self._handle_event(hotkey, event.event_type == "down")
        return handler

    def _event_loop(self) -> None:
        """串行处理真实物理边沿，保证 down/up 顺序不会被不同钩子线程打乱。"""
        while True:
            event = self._event_queue.get()
            if event is None:
                return
            with self._lock:
                listening = self._listening
            if not listening:
                continue
            hotkey, pressed, epoch = event
            with self._lock:
                current_epoch = self._config_epoch
            if epoch != current_epoch:
                continue
            self._dispatch_physical_event(hotkey, pressed)

    def _queue_physical_event(self, hotkey: str, pressed: bool) -> None:
        with self._lock:
            listening = self._listening
            if listening and self._queued_physical_state.get(hotkey) is pressed:
                return
            if listening:
                self._queued_physical_state[hotkey] = pressed
            epoch = self._config_epoch
        if listening:
            try:
                self._event_queue.put_nowait((hotkey, pressed, epoch))
            except queue.Full:
                if not self._queue_overflow_logged:
                    self._queue_overflow_logged = True
                    # hook 回调不可阻塞；溢出只记一次并依赖下一次配置/松开复位。
                    logger.warning("物理按键队列已满，已丢弃过期事件")

    @staticmethod
    def _keyboard_vk(key) -> int | None:
        vk = getattr(key, "vk", None)
        if vk is None:
            vk = getattr(getattr(key, "value", None), "vk", None)
        return int(vk) if vk is not None else None

    def _on_keyboard_press(self, key, injected: bool = False) -> None:
        self._on_keyboard_edge(key, True, injected)

    def _on_keyboard_release(self, key, injected: bool = False) -> None:
        self._on_keyboard_edge(key, False, injected)

    def _on_keyboard_edge(self, key, pressed: bool, injected: bool) -> None:
        if injected:
            return
        vk = self._keyboard_vk(key)
        hotkey = input_key_from_windows_vk(vk) if vk is not None else None
        if hotkey is not None:
            self._notify_physical_observers(hotkey, pressed, vk)
            self._queue_physical_event(hotkey, pressed)

    def _on_windows_keyboard_event(self, message: int, data) -> bool:
        """读取原始 Windows VK/down-up；不受中英文输入法字符翻译影响。"""
        if self._windows_extra_info(data) == INPUT_EVENT_MARKER:
            return True
        pressed_by_message = {
            0x0100: True,   # WM_KEYDOWN
            0x0104: True,   # WM_SYSKEYDOWN
            0x0101: False,  # WM_KEYUP
            0x0105: False,  # WM_SYSKEYUP
        }
        pressed = pressed_by_message.get(int(message))
        if pressed is None:
            return True
        vk = int(getattr(data, "vkCode", -1))
        hotkey = input_key_from_windows_vk(vk)
        if hotkey is not None:
            self._notify_physical_observers(hotkey, pressed, vk)
            self._queue_physical_event(hotkey, pressed)
        return True

    def _on_windows_mouse_event(self, message: int, data) -> bool:
        """读取原始 Windows 鼠标 down/up；只排除本程序自身 SendInput。"""
        if self._windows_extra_info(data) == INPUT_EVENT_MARKER:
            return True
        edges = {
            0x0201: ("mouse_left", True),
            0x0202: ("mouse_left", False),
            0x0204: ("mouse_right", True),
            0x0205: ("mouse_right", False),
            0x0207: ("mouse_middle", True),
            0x0208: ("mouse_middle", False),
        }
        edge = edges.get(int(message))
        if int(message) in {0x020B, 0x020C}:  # WM_XBUTTONDOWN / WM_XBUTTONUP
            button = (int(getattr(data, "mouseData", 0)) >> 16) & 0xFFFF
            hotkey = {1: "mouse_back", 2: "mouse_forward"}.get(button)
            edge = (hotkey, int(message) == 0x020B) if hotkey is not None else None
        if edge is not None:
            self._notify_physical_observers(edge[0], edge[1], None)
            self._queue_physical_event(*edge)
        return True

    @staticmethod
    def _windows_extra_info(data) -> int:
        """pynput 将空 ULONG_PTR 暴露为 None；物理输入应按 0 处理。"""
        value = getattr(data, "dwExtraInfo", 0)
        return int(value) if value is not None else 0

    def _on_mouse_click(self, _x, _y, button, pressed, injected: bool = False) -> None:
        if injected:
            return
        mapping = {
            mouse.Button.left: "mouse_left",
            mouse.Button.right: "mouse_right",
            mouse.Button.middle: "mouse_middle",
            getattr(mouse.Button, "x1", None): "mouse_back",
            getattr(mouse.Button, "x2", None): "mouse_forward",
        }
        hotkey = mapping.get(button)
        if hotkey is not None:
            self._queue_physical_event(hotkey, pressed)

    def _dispatch_physical_event(self, hotkey: str, pressed: bool) -> None:
        if hotkey == self._global_disable_key:
            self._on_global_disable_pressed(pressed)
            return
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
                # release 是恢复安全状态的幂等命令。配置刷新或队列切代可能已经
                # 清除了 press 账本，仍必须把真实松开交给按下模式停止。
                self._pressed_hotkeys.discard(hotkey)
            disabled = self._global_disabled
        with self._lock:
            suppressed = self._trigger_suppressed
        if is_pressed and (disabled or suppressed or self.is_mouse_over_window()):
            return
        callbacks: list[tuple[callable, int]] = []
        stop_callbacks: list[tuple[callable, int]] = []
        with self._lock:
            for binding in bindings:
                if self._bindings_by_id.get(binding.binding_id) is not binding:
                    continue
                if binding.mode == TriggerMode.SWITCH:
                    if not is_pressed:
                        continue
                    if binding.is_running:
                        binding.is_running = False
                        generation = self._advance_generation_locked(binding)
                        if binding.stop_callback:
                            stop_callbacks.append((binding.stop_callback, generation))
                    else:
                        binding.is_running = True
                        callbacks.append((binding.callback, self._advance_generation_locked(binding)))
                elif is_pressed:
                    if not binding.is_running:
                        binding.is_running = True
                        callbacks.append((binding.callback, self._advance_generation_locked(binding)))
                elif binding.stop_on_release:
                    # release 是幂等停止命令，不能依赖可能被旧完成回调污染的状态。
                    binding.is_running = False
                    generation = self._advance_generation_locked(binding)
                    if binding.stop_callback:
                        stop_callbacks.append((binding.stop_callback, generation))
        for callback, generation in callbacks:
            callback(generation)
        for callback, generation in stop_callbacks:
            callback(generation)

    def _on_global_disable_event(self, event) -> None:
        self._on_global_disable_pressed(event.event_type == "down")

    def _on_global_disable_pressed(self, is_pressed: bool) -> None:
        if not is_pressed:
            with self._lock:
                self._global_disable_key_pressed = False
            return
        with self._lock:
            if self._trigger_suppressed:
                return
            if self._global_disable_key_pressed:
                return
            self._global_disable_key_pressed = True
        self.toggle_global_disabled()
