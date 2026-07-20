"""Windows 单实例保护，避免多个全局 hook 同时争用同一组热键。"""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes


ERROR_ALREADY_EXISTS = 183
DEFAULT_MUTEX_NAME = r"Local\ssc8537.MyAutoPlayer"


class SingleInstanceGuard:
    def __init__(self, name: str = DEFAULT_MUTEX_NAME):
        self._name = name
        self._handle = None
        self._kernel32 = None

    def acquire(self) -> bool:
        if self._handle is not None or os.name != "nt":
            return True
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        ctypes.set_last_error(0)
        handle = kernel32.CreateMutexW(None, False, self._name)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return False
        self._kernel32 = kernel32
        self._handle = handle
        return True

    def release(self) -> None:
        handle = self._handle
        kernel32 = self._kernel32
        self._handle = None
        self._kernel32 = None
        if handle is not None and kernel32 is not None:
            kernel32.CloseHandle(handle)

    def __enter__(self) -> "SingleInstanceGuard":
        if not self.acquire():
            raise RuntimeError("自动连招已经在运行")
        return self

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self.release()


def show_already_running_message() -> None:
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(
            None,
            "自动连招已经在运行，请查看任务栏或系统托盘。",
            "自动连招",
            0x00000040,
        )
