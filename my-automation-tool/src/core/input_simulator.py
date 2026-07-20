"""输入模拟器 — 基于 Windows SendInput API 的键盘/鼠标模拟。

参考：ok-ww 项目的 send_key / click 接口设计。
首选 ctypes 调用 SendInput 保证游戏兼容性；pynput 作为 fallback。

用法：
    from src.core.input_simulator import tap_key, click_mouse, type_string
    tap_key("a")
    click_mouse("left")
    type_string("Hello World")
"""
import ctypes
import time
from ctypes import wintypes

from src.core.input_keys import is_keyboard_key, normalise_input_key, windows_vk_for_key

# ── Win32 API 常量和类型 ────────────────────────────────────────────

INPUT_KEYBOARD = 1
INPUT_MOUSE = 0

KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100

XBUTTON1 = 0x0001
XBUTTON2 = 0x0002


INPUT_EVENT_MARKER = 0x4D41504C  # "MAPL"：低级钩子只过滤本程序自己的 SendInput。
_INPUT_MARKER = INPUT_EVENT_MARKER  # 保留既有测试/内部导入名称。
_ULONG_PTR = ctypes.c_size_t


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUT_UNION)]


# ── 内部函数 ─────────────────────────────────────────────────────────

def _vk_from_key(key: str) -> int:
    """将按键名转为虚拟键码。不支持的键抛出 ValueError。"""
    try:
        canonical = normalise_input_key(key)
    except ValueError as exc:
        raise ValueError(f"不支持的按键: {key!r}") from exc
    try:
        return windows_vk_for_key(canonical)
    except ValueError as exc:
        raise ValueError(f"不支持的按键: {key!r}") from exc


def is_supported_key(key: str) -> bool:
    """返回 key 是否是本输入模拟器可发送的单个物理键。"""
    return is_keyboard_key(key)


def _send_input(*inputs: _INPUT) -> int:
    """调用 Win32 SendInput，返回成功发送的事件数。"""
    n = len(inputs)
    if n == 0:
        return 0
    arr = (_INPUT * n)(*inputs)
    return ctypes.windll.user32.SendInput(n, arr, ctypes.sizeof(_INPUT))


def _make_kb_input(vk: int, flags: int = KEYEVENTF_KEYDOWN) -> _INPUT:
    """构造键盘 INPUT 结构。"""
    inp = _INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk
    # 与优秀案例 1 一致，同时提供 VK 与物理扫描码；目标程序仍按真实物理键处理。
    inp.union.ki.wScan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
    inp.union.ki.dwFlags = flags
    inp.union.ki.time = 0
    inp.union.ki.dwExtraInfo = INPUT_EVENT_MARKER
    return inp


def _make_unicode_input(char: str, down: bool = True) -> _INPUT:
    """构造 Unicode 字符 INPUT 结构（用于打字）。"""
    inp = _INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = 0
    inp.union.ki.wScan = ord(char)
    inp.union.ki.dwFlags = KEYEVENTF_UNICODE
    if not down:
        inp.union.ki.dwFlags |= KEYEVENTF_KEYUP
    inp.union.ki.time = 0
    inp.union.ki.dwExtraInfo = INPUT_EVENT_MARKER
    return inp


def _make_mouse_input(flags: int, data: int = 0) -> _INPUT:
    """构造鼠标 INPUT 结构。"""
    inp = _INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.dx = 0
    inp.union.mi.dy = 0
    inp.union.mi.mouseData = data
    inp.union.mi.dwFlags = flags
    inp.union.mi.time = 0
    inp.union.mi.dwExtraInfo = INPUT_EVENT_MARKER
    return inp


# ── 公开 API ─────────────────────────────────────────────────────────

def press_key(key: str) -> None:
    """按下按键（不释放）。"""
    _send_input(_make_kb_input(_vk_from_key(key), KEYEVENTF_KEYDOWN))


def release_key(key: str) -> None:
    """释放按键。"""
    _send_input(_make_kb_input(_vk_from_key(key), KEYEVENTF_KEYUP))


def tap_key(key: str, duration: float = 0.05) -> None:
    """按下并释放按键，中间间隔 duration 秒（默认 50ms）。

    游戏需要精确的按键持续时间，太短可能不被识别。
    """
    press_key(key)
    time.sleep(duration)
    release_key(key)


def hold_key(key: str, duration: float) -> None:
    """按住按键 duration 秒后释放。"""
    press_key(key)
    time.sleep(duration)
    release_key(key)


def click_mouse(button: str = "left") -> None:
    """点击鼠标（按下 + 释放），默认左键。

    button 可选: "left", "right", "middle", "x1", "x2"
    """
    flags_down = {
        "left": MOUSEEVENTF_LEFTDOWN,
        "right": MOUSEEVENTF_RIGHTDOWN,
        "middle": MOUSEEVENTF_MIDDLEDOWN,
        "x1": MOUSEEVENTF_XDOWN,
        "x2": MOUSEEVENTF_XDOWN,
    }
    flags_up = {
        "left": MOUSEEVENTF_LEFTUP,
        "right": MOUSEEVENTF_RIGHTUP,
        "middle": MOUSEEVENTF_MIDDLEUP,
        "x1": MOUSEEVENTF_XUP,
        "x2": MOUSEEVENTF_XUP,
    }
    data = XBUTTON1 if button == "x1" else XBUTTON2 if button == "x2" else 0
    fl_down = flags_down.get(button)
    fl_up = flags_up.get(button)
    if fl_down is None:
        raise ValueError(f"不支持的鼠标按钮: {button!r}")
    _send_input(_make_mouse_input(fl_down, data))
    time.sleep(0.01)
    _send_input(_make_mouse_input(fl_up, data))


def mouse_down(button: str = "left") -> None:
    """按下鼠标键（不释放）。"""
    flags = {
        "left": MOUSEEVENTF_LEFTDOWN,
        "right": MOUSEEVENTF_RIGHTDOWN,
        "middle": MOUSEEVENTF_MIDDLEDOWN,
        "x1": MOUSEEVENTF_XDOWN,
        "x2": MOUSEEVENTF_XDOWN,
    }
    fl = flags.get(button)
    if fl is None:
        raise ValueError(f"不支持的鼠标按钮: {button!r}")
    data = XBUTTON1 if button == "x1" else XBUTTON2 if button == "x2" else 0
    _send_input(_make_mouse_input(fl, data))


def mouse_up(button: str = "left") -> None:
    """释放鼠标键。"""
    flags = {
        "left": MOUSEEVENTF_LEFTUP,
        "right": MOUSEEVENTF_RIGHTUP,
        "middle": MOUSEEVENTF_MIDDLEUP,
        "x1": MOUSEEVENTF_XUP,
        "x2": MOUSEEVENTF_XUP,
    }
    fl = flags.get(button)
    if fl is None:
        raise ValueError(f"不支持的鼠标按钮: {button!r}")
    data = XBUTTON1 if button == "x1" else XBUTTON2 if button == "x2" else 0
    _send_input(_make_mouse_input(fl, data))


def type_string(
    text: str, interval: float = 0.01,
    stop_event=None,
) -> bool:
    """模拟键盘打字，逐个字符输出，支持在字符间立即取消。

    Hello World 验证的核心函数。每个字符之间间隔 interval 秒。
    返回 True 表示完整输出，False 表示被 stop_event 中断。
    """
    for ch in text:
        if stop_event is not None and stop_event.is_set():
            return False
        _send_input(_make_unicode_input(ch, down=True))
        if stop_event is not None:
            interrupted = stop_event.wait(interval)
        else:
            time.sleep(interval)
            interrupted = False
        _send_input(_make_unicode_input(ch, down=False))
        if interrupted:
            return False
        if stop_event is not None:
            if stop_event.wait(0.005):
                return False
        else:
            time.sleep(0.005)
    return True
