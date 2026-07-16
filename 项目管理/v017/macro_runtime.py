"""为固定 JSON 宏提供线程安全的按触发重载。"""
from __future__ import annotations

import threading
from pathlib import Path

from src.core.macro_loader import TestMacro, load_test_macro


class MacroRuntime:
    """保存最近一次有效宏，并在每次启动前从磁盘重新加载。"""

    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._lock = threading.RLock()
        self._macro = load_test_macro(self._path)

    def current(self) -> TestMacro:
        with self._lock:
            return self._macro

    def reload(self) -> TestMacro:
        """验证成功后原子替换当前宏；验证失败时保留上一次有效值。"""
        macro = load_test_macro(self._path)
        with self._lock:
            self._macro = macro
            return macro
