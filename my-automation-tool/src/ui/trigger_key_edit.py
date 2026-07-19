"""触发页的单键录入框；仅录入，不发送或拦截真实输入。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QKeySequence, QMouseEvent
from PySide6.QtWidgets import QLineEdit


_SPECIAL_KEYS = {
    Qt.Key.Key_Escape: "esc", Qt.Key.Key_Tab: "tab", Qt.Key.Key_Backspace: "backspace",
    Qt.Key.Key_Return: "enter", Qt.Key.Key_Enter: "enter", Qt.Key.Key_Insert: "insert",
    Qt.Key.Key_Delete: "delete", Qt.Key.Key_Home: "home", Qt.Key.Key_End: "end",
    Qt.Key.Key_Left: "left", Qt.Key.Key_Up: "up", Qt.Key.Key_Right: "right",
    Qt.Key.Key_Down: "down", Qt.Key.Key_PageUp: "page up", Qt.Key.Key_PageDown: "page down",
    Qt.Key.Key_Space: "space",
    Qt.Key.Key_CapsLock: "caps lock", Qt.Key.Key_NumLock: "num lock",
    Qt.Key.Key_ScrollLock: "scroll lock", Qt.Key.Key_Pause: "pause",
    Qt.Key.Key_Print: "print screen", Qt.Key.Key_Menu: "menu",
    Qt.Key.Key_Shift: "shift", Qt.Key.Key_Control: "ctrl", Qt.Key.Key_Alt: "alt",
    Qt.Key.Key_Meta: "win", Qt.Key.Key_Help: "help",
}
for _number in range(1, 36):
    _SPECIAL_KEYS[getattr(Qt.Key, f"Key_F{_number}")] = f"f{_number}"


def display_hotkey(hotkey: str) -> str:
    """沿用优秀案例 1 QKeyEdit::keyName 的面向用户名称。"""
    names = {
        "mouse_left": "左键", "mouse_right": "右键", "mouse_middle": "中键",
        "mouse_back": "侧键1", "mouse_forward": "侧键2", "space": "空格",
        "esc": "Esc", "tab": "Tab", "backspace": "Back", "enter": "Return",
        "page up": "PageUp", "page down": "PageDown", "left": "←", "up": "↑",
        "right": "→", "down": "↓", "delete": "Delete", "insert": "Insert",
        "home": "Home", "end": "End",
    }
    return names.get(hotkey, hotkey.upper())


def hotkey_from_display(value: str) -> str:
    """把案例显示名还原为内部监听名，避免编辑其他字段时改坏热键。"""
    reverse = {
        "左键": "mouse_left", "右键": "mouse_right", "中键": "mouse_middle",
        "侧键1": "mouse_back", "侧键2": "mouse_forward", "空格": "space",
        "Esc": "esc", "Tab": "tab", "Back": "backspace", "Return": "enter",
        "PageUp": "page up", "PageDown": "page down", "←": "left", "↑": "up",
        "→": "right", "↓": "down", "Delete": "delete", "Insert": "insert",
        "Home": "home", "End": "end",
    }
    return reverse.get(value, value.lower())


class TriggerKeyEdit(QLineEdit):
    """点击后等待一个键盘键或鼠标后退/前进侧键。"""

    hotkey_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._capturing = False
        self.setReadOnly(True)
        self.setPlaceholderText("点击后按键")

    def set_hotkey(self, hotkey: str) -> None:
        self._capturing = False
        self.setText(display_hotkey(hotkey))

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
        if event.button() == Qt.MouseButton.BackButton:
            self._finish("mouse_back")
            return
        if event.button() == Qt.MouseButton.ForwardButton:
            self._finish("mouse_forward")
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._capturing = True
            self.clear()
            self.setPlaceholderText("请按键盘键或鼠标侧键…")
            self.setFocus()
            event.accept()
            return
        event.accept()


    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self._capturing:
            event.accept()
            return
        hotkey = _SPECIAL_KEYS.get(event.key())
        if hotkey is None and event.text() and not event.modifiers():
            hotkey = event.text().lower()
        if hotkey is None:
            # Qt 能识别的其余单键（媒体键、浏览器键等）也交给 keyboard 库注册。
            sequence = QKeySequence(event.key()).toString()
            if sequence and "+" not in sequence:
                hotkey = sequence.lower()
        if hotkey is None:
            self.setPlaceholderText("请按一个键，不支持组合键")
            event.accept()
            return
        if hotkey == "f12":
            self.setPlaceholderText("F12 是全局停止键")
            event.accept()
            return
        self._finish(hotkey)
        event.accept()

    def _finish(self, hotkey: str) -> None:
        self._capturing = False
        self.setText(display_hotkey(hotkey))
        self.hotkey_selected.emit(hotkey)
