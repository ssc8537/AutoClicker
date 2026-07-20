"""Stage 7A shared single-key names for capture, hooks, and SendInput."""
from __future__ import annotations

MOUSE_HOTKEYS = frozenset(
    {"mouse_left", "mouse_right", "mouse_middle", "mouse_back", "mouse_forward"}
)

MOUSE_BUTTON_FOR_HOTKEY = {
    "mouse_left": "left",
    "mouse_right": "right",
    "mouse_middle": "middle",
    "mouse_back": "x1",
    "mouse_forward": "x2",
}

_PUNCTUATION_ALIASES = {
    "`": "backquote",
    "grave": "backquote",
    "~": "backquote",
    "-": "minus",
    "=": "equals",
    "[": "left bracket",
    "]": "right bracket",
    "\\": "backslash",
    ";": "semicolon",
    "'": "quote",
    ",": "comma",
    ".": "period",
    "/": "slash",
}

_KEY_ALIASES = {
    " ": "space",
    "return": "enter",
    "escape": "esc",
    "pageup": "page up",
    "pagedown": "page down",
    "capslock": "caps lock",
    "numlock": "num lock",
    "scrolllock": "scroll lock",
    "print": "print screen",
    "snapshot": "print screen",
    "control": "ctrl",
    "windows": "win",
    "lwin": "left win",
    "rwin": "right win",
    "lctrl": "left ctrl",
    "rctrl": "right ctrl",
    "lshift": "left shift",
    "rshift": "right shift",
    "lalt": "left alt",
    "ralt": "right alt",
}

KEYBOARD_KEYS = frozenset(
    {
        *(chr(code) for code in range(ord("a"), ord("z") + 1)),
        *(str(number) for number in range(10)),
        *(f"f{number}" for number in range(1, 25)),
        *(f"numpad{number}" for number in range(10)),
        "space", "enter", "esc", "tab", "backspace", "insert", "delete",
        "home", "end", "page up", "page down", "left", "up", "right", "down",
        "caps lock", "num lock", "scroll lock", "pause", "print screen", "menu",
        "shift", "ctrl", "alt", "win", "left shift", "right shift", "left ctrl",
        "right ctrl", "left alt", "right alt", "left win", "right win",
        "numpad multiply", "numpad add", "numpad subtract", "numpad decimal",
        "numpad divide", "backquote", "minus", "equals", "left bracket",
        "right bracket", "backslash", "semicolon", "quote", "comma", "period", "slash",
    }
)

# Windows 虚拟键码是输入发送与全局监听之间的唯一物理键契约。
# 两边共用同一张表，避免“能发送但监听不到”或名称漂移。
WINDOWS_VK_BY_KEY: dict[str, int] = {
    **{str(number): 0x30 + number for number in range(10)},
    **{chr(code): 0x41 + code - ord("a") for code in range(ord("a"), ord("z") + 1)},
    **{f"f{number}": 0x6F + number for number in range(1, 25)},
    **{f"numpad{number}": 0x60 + number for number in range(10)},
    "space": 0x20, "enter": 0x0D, "esc": 0x1B, "tab": 0x09,
    "backspace": 0x08, "delete": 0x2E, "insert": 0x2D,
    "home": 0x24, "end": 0x23, "page up": 0x21, "page down": 0x22,
    "caps lock": 0x14, "num lock": 0x90, "scroll lock": 0x91,
    "pause": 0x13, "print screen": 0x2C, "menu": 0x5D,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "ctrl": 0x11, "shift": 0x10, "alt": 0x12, "win": 0x5B,
    "left ctrl": 0xA2, "right ctrl": 0xA3,
    "left shift": 0xA0, "right shift": 0xA1,
    "left alt": 0xA4, "right alt": 0xA5,
    "left win": 0x5B, "right win": 0x5C,
    "numpad multiply": 0x6A, "numpad add": 0x6B,
    "numpad subtract": 0x6D, "numpad decimal": 0x6E,
    "numpad divide": 0x6F, "backquote": 0xC0, "minus": 0xBD,
    "equals": 0xBB, "left bracket": 0xDB, "right bracket": 0xDD,
    "backslash": 0xDC, "semicolon": 0xBA, "quote": 0xDE,
    "comma": 0xBC, "period": 0xBE, "slash": 0xBF,
}

# 通用修饰键与左侧修饰键共享 VK；监听时优先保留明确的左右键名。
INPUT_KEY_BY_WINDOWS_VK = {
    vk: key for key, vk in WINDOWS_VK_BY_KEY.items()
    if key not in {"ctrl", "shift", "alt", "win"}
}

_DISPLAY_NAMES = {
    "mouse_left": "左键", "mouse_right": "右键", "mouse_middle": "中键",
    "mouse_back": "侧键1", "mouse_forward": "侧键2", "space": "空格",
    "esc": "Esc", "tab": "Tab", "backspace": "Back", "enter": "Enter",
    "page up": "PageUp", "page down": "PageDown", "left": "←", "up": "↑",
    "right": "→", "down": "↓", "delete": "Delete", "insert": "Insert",
    "home": "Home", "end": "End", "caps lock": "CapsLock", "num lock": "NumLock",
    "scroll lock": "ScrollLock", "print screen": "PrintScreen", "backquote": "· / `",
    "minus": "-", "equals": "=", "left bracket": "[", "right bracket": "]",
    "backslash": "\\", "semicolon": ";", "quote": "'", "comma": ",",
    "period": ".", "slash": "/", "shift": "Shift", "ctrl": "Ctrl", "alt": "Alt",
    "win": "Win", "left shift": "左 Shift", "right shift": "右 Shift",
    "left ctrl": "左 Ctrl", "right ctrl": "右 Ctrl", "left alt": "左 Alt",
    "right alt": "右 Alt", "left win": "左 Win", "right win": "右 Win",
}


def normalise_input_key(value: object) -> str:
    """Return one supported physical key name or raise ValueError."""
    if not isinstance(value, str):
        raise ValueError("按键必须是单个标准键盘键或鼠标按钮")
    key = value.strip().lower()
    key = _PUNCTUATION_ALIASES.get(key, _KEY_ALIASES.get(key, key))
    if key in KEYBOARD_KEYS or key in MOUSE_HOTKEYS:
        return key
    raise ValueError("不支持的按键；请选择一个标准键盘键或鼠标左/右/中/侧键")


def is_keyboard_key(value: object) -> bool:
    try:
        return normalise_input_key(value) in KEYBOARD_KEYS
    except ValueError:
        return False


def display_input_key(value: str) -> str:
    """Use the concise user-facing names from the reference's key editor."""
    key = normalise_input_key(value)
    return _DISPLAY_NAMES.get(key, key.upper())


def keyboard_hook_name(key: str) -> str:
    """Translate persistent names to the spelling accepted by ``keyboard``."""
    canonical = normalise_input_key(key)
    if canonical == "backquote":
        return "`"
    return canonical


def windows_vk_for_key(key: str) -> int:
    """Return the Windows virtual-key code for one supported keyboard key."""
    canonical = normalise_input_key(key)
    try:
        return WINDOWS_VK_BY_KEY[canonical]
    except KeyError as exc:
        raise ValueError(f"不支持的键盘键: {key!r}") from exc


def input_key_from_windows_vk(vk: int) -> str | None:
    """Translate a physical Windows key event back to the persistent name."""
    return INPUT_KEY_BY_WINDOWS_VK.get(int(vk))
