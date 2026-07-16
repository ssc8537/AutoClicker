"""提供给可信 Python 宏的最小、可中断输入 API。"""
from __future__ import annotations

import threading
from collections.abc import Callable

from src.core.input_simulator import is_supported_key, press_key, release_key


class ScriptInterrupted(Exception):
    """表示用户松开热键、按 F12 或关闭窗口导致的正常中断。"""


class ScriptPlayer:
    """脚本作者只使用 tap() 与 sleep()，不直接接触线程或 SendInput。"""

    def __init__(
        self,
        stop_event: threading.Event,
        speed: float,
        press: Callable[[str], None] = press_key,
        release: Callable[[str], None] = release_key,
    ):
        self._stop_event = stop_event
        self._speed = speed
        self._press = press
        self._release = release

    def tap(self, key: str, hold_ms: int = 20) -> None:
        """现实键盘按下并释放一个单键；中断时仍保证释放。"""
        if not is_supported_key(key):
            raise ValueError(f"不支持的物理按键: {key!r}")
        if isinstance(hold_ms, bool) or not isinstance(hold_ms, int) or hold_ms < 1:
            raise ValueError("hold_ms 必须是大于 0 的整数")
        self._raise_if_stopped()
        pressed = False
        interrupted = False
        try:
            self._press(key)
            pressed = True
            interrupted = self._stop_event.wait(hold_ms / 1000.0)
        finally:
            if pressed:
                self._release(key)
        if interrupted:
            raise ScriptInterrupted()

    def sleep(self, ms: int | float) -> None:
        """按该宏速度倍率等待；用户停止时立即退出脚本。"""
        if isinstance(ms, bool) or not isinstance(ms, (int, float)) or ms < 0:
            raise ValueError("ms 必须是非负数字")
        self._raise_if_stopped()
        if self._stop_event.wait(float(ms) / self._speed / 1000.0):
            raise ScriptInterrupted()

    def _raise_if_stopped(self) -> None:
        if self._stop_event.is_set():
            raise ScriptInterrupted()
