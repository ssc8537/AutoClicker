"""Reusable one-key capture box; capture never sends or blocks real input."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QLineEdit

from src.core.input_keys import display_input_key, normalise_input_key


_SPECIAL_KEYS = {
    Qt.Key.Key_Escape: "esc", Qt.Key.Key_Tab: "tab", Qt.Key.Key_Backspace: "backspace",
    Qt.Key.Key_Return: "enter", Qt.Key.Key_Enter: "enter", Qt.Key.Key_Insert: "insert",
    Qt.Key.Key_Delete: "delete", Qt.Key.Key_Home: "home", Qt.Key.Key_End: "end",
    Qt.Key.Key_Left: "left", Qt.Key.Key_Up: "up", Qt.Key.Key_Right: "right",
    Qt.Key.Key_Down: "down", Qt.Key.Key_PageUp: "page up", Qt.Key.Key_PageDown: "page down",
    Qt.Key.Key_Space: "space", Qt.Key.Key_CapsLock: "caps lock",
    Qt.Key.Key_NumLock: "num lock", Qt.Key.Key_ScrollLock: "scroll lock",
    Qt.Key.Key_Pause: "pause", Qt.Key.Key_Print: "print screen", Qt.Key.Key_Menu: "menu",
    Qt.Key.Key_Shift: "shift", Qt.Key.Key_Control: "ctrl", Qt.Key.Key_Alt: "alt",
    Qt.Key.Key_Meta: "win",
    Qt.Key.Key_QuoteLeft: "backquote", Qt.Key.Key_Minus: "minus", Qt.Key.Key_Equal: "equals",
    Qt.Key.Key_BracketLeft: "left bracket", Qt.Key.Key_BracketRight: "right bracket",
    Qt.Key.Key_Backslash: "backslash", Qt.Key.Key_Semicolon: "semicolon",
    Qt.Key.Key_Apostrophe: "quote", Qt.Key.Key_Comma: "comma", Qt.Key.Key_Period: "period",
    Qt.Key.Key_Slash: "slash",
}
for _number in range(1, 25):
    _SPECIAL_KEYS[getattr(Qt.Key, f"Key_F{_number}")] = f"f{_number}"
for _number in range(10):
    _SPECIAL_KEYS[getattr(Qt.Key, f"Key_{_number}")] = str(_number)


def display_hotkey(hotkey: str) -> str:
    """Compatibility name for existing trigger-table callers."""
    return display_input_key(hotkey)


def hotkey_from_display(value: str) -> str:
    """Compatibility parser; persistent fields are normally set by ``set_hotkey``."""
    try:
        return normalise_input_key(value)
    except ValueError:
        displayed = {
            display_input_key(key): key
            for key in (
                "mouse_left", "mouse_right", "mouse_middle", "mouse_back", "mouse_forward",
                "space", "esc", "tab", "backspace", "enter", "page up", "page down",
                "left", "up", "right", "down", "delete", "insert", "home", "end", "backquote",
            )
        }
        return displayed.get(value, value.lower())


class TriggerKeyEdit(QLineEdit):
    """Click once, then press exactly one keyboard key or mouse button."""

    hotkey_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._capturing = False
        self._hotkey = ""
        self.setReadOnly(True)
        self.setPlaceholderText("点击后按键")

    def hotkey(self) -> str:
        return self._hotkey

    def set_hotkey(self, hotkey: str) -> None:
        self._capturing = False
        self._hotkey = normalise_input_key(hotkey)
        self.setText(display_input_key(self._hotkey))
        self.setPlaceholderText("点击后按键")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._capturing:
            mapping = {
                Qt.MouseButton.LeftButton: "mouse_left",
                Qt.MouseButton.RightButton: "mouse_right",
                Qt.MouseButton.MiddleButton: "mouse_middle",
                Qt.MouseButton.BackButton: "mouse_back",
                Qt.MouseButton.ForwardButton: "mouse_forward",
            }
            hotkey = mapping.get(event.button())
            if hotkey is not None:
                self._finish(hotkey)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._capturing = True
            self.clear()
            self.setPlaceholderText("请按一个键或鼠标按钮…")
            self.setFocus()
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self._capturing:
            event.accept()
            return
        hotkey = _SPECIAL_KEYS.get(event.key())
        if (
            hotkey is not None
            and hotkey.isdigit()
            and event.modifiers() & Qt.KeyboardModifier.KeypadModifier
        ):
            hotkey = f"numpad{hotkey}"
        if hotkey is None and event.text() and not event.modifiers():
            hotkey = event.text().lower()
        if hotkey is None:
            self.setPlaceholderText("请按一个键，不支持组合键")
            event.accept()
            return
        try:
            self._finish(hotkey)
        except ValueError:
            self.setPlaceholderText("该键不在支持范围，请换一个键")
        event.accept()

    def _finish(self, hotkey: str) -> None:
        self._hotkey = normalise_input_key(hotkey)
        self._capturing = False
        self.setText(display_input_key(self._hotkey))
        self.setPlaceholderText("点击后按键")
        self.hotkey_selected.emit(self._hotkey)
