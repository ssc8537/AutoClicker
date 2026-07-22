"""Windows 单实例保护，避免多个全局 hook 同时争用同一组热键。"""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes


ERROR_ALREADY_EXISTS = 183
DEFAULT_MUTEX_NAME = r"Local\ssc8537.MyAutoPlayer"
WAIT_OBJECT_0 = 0


class SingleInstanceGuard:
    def __init__(self, name: str = DEFAULT_MUTEX_NAME):
        self._name = name
        self._activation_name = name + ".Activate"
        self._handle = None
        self._activation_handle = None
        self._kernel32 = None

    def acquire(self) -> bool:
        if self._handle is not None or os.name != "nt":
            return True
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.CreateEventW.argtypes = (
            ctypes.c_void_p,
            wintypes.BOOL,
            wintypes.BOOL,
            wintypes.LPCWSTR,
        )
        kernel32.CreateEventW.restype = wintypes.HANDLE
        kernel32.SetEvent.argtypes = (wintypes.HANDLE,)
        kernel32.SetEvent.restype = wintypes.BOOL
        kernel32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        kernel32.WaitForSingleObject.restype = wintypes.DWORD
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        activation_handle = kernel32.CreateEventW(
            None, False, False, self._activation_name
        )
        if not activation_handle:
            raise ctypes.WinError(ctypes.get_last_error())
        ctypes.set_last_error(0)
        handle = kernel32.CreateMutexW(None, False, self._name)
        if not handle:
            kernel32.CloseHandle(activation_handle)
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            kernel32.SetEvent(activation_handle)
            kernel32.CloseHandle(handle)
            kernel32.CloseHandle(activation_handle)
            return False
        self._kernel32 = kernel32
        self._handle = handle
        self._activation_handle = activation_handle
        return True

    def consume_activation_request(self) -> bool:
        """第一实例消费第二次启动发出的自动复位唤醒事件。"""
        if os.name != "nt":
            return False
        if self._activation_handle is None or self._kernel32 is None:
            return False
        return (
            self._kernel32.WaitForSingleObject(self._activation_handle, 0)
            == WAIT_OBJECT_0
        )

    def release(self) -> None:
        handle = self._handle
        activation_handle = self._activation_handle
        kernel32 = self._kernel32
        self._handle = None
        self._activation_handle = None
        self._kernel32 = None
        if handle is not None and kernel32 is not None:
            kernel32.CloseHandle(handle)
        if activation_handle is not None and kernel32 is not None:
            kernel32.CloseHandle(activation_handle)

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
