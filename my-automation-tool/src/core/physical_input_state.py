"""保存 Windows 全局钩子确认过的真实物理按键状态。"""
from __future__ import annotations

import threading

from src.core.input_keys import normalise_input_key


class PhysicalInputState:
    """线程安全地共享物理 down/up；本程序 MAPL 模拟输入不会写入这里。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._pressed: set[str] = set()

    def update(self, key: str, pressed: bool) -> None:
        canonical = normalise_input_key(key)
        with self._lock:
            if pressed:
                self._pressed.add(canonical)
            else:
                self._pressed.discard(canonical)

    def is_pressed(self, key: str) -> bool:
        canonical = normalise_input_key(key)
        with self._lock:
            return canonical in self._pressed

    def clear(self) -> None:
        with self._lock:
            self._pressed.clear()


physical_input_state = PhysicalInputState()
