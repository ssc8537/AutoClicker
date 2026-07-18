"""提供给可信 Python 宏的最小、可中断输入 API。"""
from __future__ import annotations

import threading
from collections.abc import Callable

from src.core.input_simulator import (
    is_supported_key,
    mouse_down as press_mouse,
    mouse_up as release_mouse,
    press_key,
    release_key,
)
from src.core.game_keybinds import DEFAULT_GAME_KEYBINDS, GameKeybinds


class ScriptInterrupted(Exception):
    """表示用户松开热键、按 F12 或关闭窗口导致的正常中断。"""


class ScriptPlayer:
    """脚本作者只使用受控输入 API，不直接接触线程或 SendInput。"""

    _MOUSE_BUTTONS = frozenset({"left", "right"})

    def __init__(
        self,
        stop_event: threading.Event,
        speed: float,
        press: Callable[[str], None] = press_key,
        release: Callable[[str], None] = release_key,
        keybinds: GameKeybinds = DEFAULT_GAME_KEYBINDS,
        mouse_press: Callable[[str], None] = press_mouse,
        mouse_release: Callable[[str], None] = release_mouse,
    ):
        self._stop_event = stop_event
        self._speed = speed
        self._press = press
        self._release = release
        self._keybinds = keybinds
        self._mouse_press = mouse_press
        self._mouse_release = mouse_release
        self._held_mouse_buttons: set[str] = set()

    def 切换(self, character: int) -> None:
        """发送用户配置的角色 1、2 或 3 物理键，不检测游戏角色状态。"""
        if isinstance(character, bool) or character not in {1, 2, 3}:
            raise ValueError("切换只接受角色编号 1、2 或 3")
        self.tap(self._keybinds.key_for(f"character_{character}"))

    def 战技(self) -> None:
        self.tap(self._keybinds.key_for("skill"))

    def 声骸(self) -> None:
        self.tap(self._keybinds.key_for("echo"))

    def 大招(self) -> None:
        self.tap(self._keybinds.key_for("ultimate"))

    def 跳跃(self) -> None:
        self.tap(self._keybinds.key_for("jump"))

    def 处决(self) -> None:
        self.tap(self._keybinds.key_for("execute"))

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

    def mouse_down(self, button: str = "left") -> None:
        """按住当前鼠标位置的左键或右键；重复按下同一键不会重复发送。"""
        self._validate_mouse_button(button)
        self._raise_if_stopped()
        if button not in self._held_mouse_buttons:
            self._mouse_press(button)
            self._held_mouse_buttons.add(button)

    def mouse_up(self, button: str = "left") -> None:
        """松开本播放器此前按住的左键或右键；重复松开是幂等的。"""
        self._validate_mouse_button(button)
        if button in self._held_mouse_buttons:
            try:
                self._mouse_release(button)
            finally:
                self._held_mouse_buttons.discard(button)

    def mouse_click(self, button: str = "left", hold_ms: int = 10) -> None:
        """左键或右键单击；中断时仍在 finally 中松开。"""
        self._validate_mouse_button(button)
        self._validate_positive_int(hold_ms, "hold_ms")
        self.mouse_down(button)
        interrupted = False
        try:
            interrupted = self._stop_event.wait(hold_ms / 1000.0)
        finally:
            self.mouse_up(button)
        if interrupted:
            raise ScriptInterrupted()

    def mouse_repeat(
        self, count: int, button: str = "left", interval_ms: int = 10,
    ) -> None:
        """有限重复单击：1–100 次，点击之间至少等待 10ms。"""
        self._validate_mouse_button(button)
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 100:
            raise ValueError("count 必须是 1 到 100 的整数")
        if (
            isinstance(interval_ms, bool)
            or not isinstance(interval_ms, int)
            or interval_ms < 10
        ):
            raise ValueError("interval_ms 必须是大于等于 10 的整数")
        for index in range(count):
            self.mouse_click(button)
            if index < count - 1:
                if self._stop_event.wait(interval_ms / 1000.0):
                    raise ScriptInterrupted()

    def release_held_mouse_buttons(self) -> None:
        """执行轮次清理：释放本播放器仍持有的鼠标键。"""
        for button in tuple(self._held_mouse_buttons):
            self.mouse_up(button)

    @classmethod
    def _validate_mouse_button(cls, button: str) -> None:
        if not isinstance(button, str) or button not in cls._MOUSE_BUTTONS:
            raise ValueError('button 只支持 "left" 或 "right"')

    @staticmethod
    def _validate_positive_int(value: int, name: str) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} 必须是大于 0 的整数")

    def _raise_if_stopped(self) -> None:
        if self._stop_event.is_set():
            raise ScriptInterrupted()
