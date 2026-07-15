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


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUT_UNION)]


# ── 虚拟键码映射表 ───────────────────────────────────────────────────

_VK_MAP: dict[str, int] = {
    # 数字键
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
    # 字母键
    "a": 0x41, "b": 0x42, "c": 0x43, "d": 0x44, "e": 0x45,
    "f": 0x46, "g": 0x47, "h": 0x48, "i": 0x49, "j": 0x4A,
    "k": 0x4B, "l": 0x4C, "m": 0x4D, "n": 0x4E, "o": 0x4F,
    "p": 0x50, "q": 0x51, "r": 0x52, "s": 0x53, "t": 0x54,
    "u": 0x55, "v": 0x56, "w": 0x57, "x": 0x58, "y": 0x59,
    "z": 0x5A,
    # 功能键
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    # 特殊键
    "space": 0x20, "enter": 0x0D, "esc": 0x1B, "escape": 0x1B,
    "tab": 0x09, "backspace": 0x08, "delete": 0x2E, "insert": 0x2D,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "capslock": 0x14, "numlock": 0x90, "scrolllock": 0x91,
    # 方向键
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    # 修饰键
    "ctrl": 0x11, "shift": 0x10, "alt": 0x12,
    "lctrl": 0xA2, "rctrl": 0xA3,
    "lshift": 0xA0, "rshift": 0xA1,
    "lalt": 0xA4, "ralt": 0xA5,
    "lwin": 0x5B, "rwin": 0x5C,
    # 符号通过 Unicode 发送
    # 媒体键
    "volumemute": 0xAD, "volumedown": 0xAE, "volumeup": 0xAF,
    "medianext": 0xB0, "mediaprev": 0xB1, "mediastop": 0xB2,
    "mediaplay": 0xB3,
}

# ── 内部函数 ─────────────────────────────────────────────────────────

def _vk_from_key(key: str) -> int:
    """将按键名转为虚拟键码。不支持的键抛出 ValueError。"""
    vk = _VK_MAP.get(key.lower())
    if vk is None:
        raise ValueError(f"不支持的按键: {key!r}")
    return vk


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
    inp.union.ki.wScan = 0
    inp.union.ki.dwFlags = flags
    inp.union.ki.time = 0
    inp.union.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
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
    inp.union.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
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
    inp.union.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
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
    }
    fl = flags.get(button)
    if fl is None:
        raise ValueError(f"不支持的鼠标按钮: {button!r}")
    _send_input(_make_mouse_input(fl))


def mouse_up(button: str = "left") -> None:
    """释放鼠标键。"""
    flags = {
        "left": MOUSEEVENTF_LEFTUP,
        "right": MOUSEEVENTF_RIGHTUP,
        "middle": MOUSEEVENTF_MIDDLEUP,
    }
    fl = flags.get(button)
    if fl is None:
        raise ValueError(f"不支持的鼠标按钮: {button!r}")
    _send_input(_make_mouse_input(fl))


def type_string(text: str, interval: float = 0.01) -> None:
    """模拟键盘打字，逐个字符输出。

    Hello World 验证的核心函数。每个字符之间间隔 interval 秒。
    """
    for ch in text:
        _send_input(_make_unicode_input(ch, down=True))
        time.sleep(interval)
        _send_input(_make_unicode_input(ch, down=False))
        time.sleep(0.005)
