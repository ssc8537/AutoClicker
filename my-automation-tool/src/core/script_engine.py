"""阶段 3 的单可信 Python 宏加载、校验和执行。"""
from __future__ import annotations

import threading
import inspect
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from src.core.script_player import ScriptInterrupted, ScriptPlayer
from src.core.game_keybinds import GameKeybinds, load_game_keybinds


class PythonMacroValidationError(ValueError):
    """Python 宏文件无法加载或不符合约定。"""


@dataclass(frozen=True)
class PythonMacro:
    name: str
    hotkey: str
    mode: str
    count: int
    speed: float
    run: object


class PythonMacroRuntime:
    """保存最后一次有效 Python 宏，并在 F9 前原子重载。"""

    def __init__(self, path: str | Path | None = None):
        self._path = Path(path) if path is not None else None
        self._lock = threading.RLock()
        self._macro = None

    def current(self) -> PythonMacro | None:
        with self._lock:
            return self._macro

    def selected_path(self) -> Path | None:
        """返回活动路径，但不加载或执行该宏。"""
        with self._lock:
            return self._path

    def set_selected_path(self, path: str | Path | None) -> None:
        """设置活动路径，实际加载只允许发生在 F9 的 reload 中。"""
        with self._lock:
            self._path = Path(path) if path is not None else None
            self._macro = None

    def reload(self) -> PythonMacro:
        if self._path is None:
            raise PythonMacroValidationError("未选择有效宏")
        macro = load_python_macro(self._path)
        with self._lock:
            self._macro = macro
            return macro


def load_python_macro(path: str | Path) -> PythonMacro:
    """加载一个可信本地 Python 文件，并验证阶段 3 的固定接口。"""
    script_path = Path(path)
    if not script_path.is_file():
        raise PythonMacroValidationError(f"找不到 Python 宏文件: {script_path}")
    module = ModuleType(f"my_auto_macro_{script_path.stat().st_mtime_ns}")
    module.__file__ = str(script_path)
    try:
        # 直接读取源码，避免 importlib 在快速保存同长度文件时复用旧 .pyc。
        source = script_path.read_text(encoding="utf-8-sig")
        exec(compile(source, str(script_path), "exec"), module.__dict__)
    except Exception as exc:
        raise PythonMacroValidationError(f"Python 宏加载失败: {exc}") from exc

    name = getattr(module, "NAME", None)
    hotkey = getattr(module, "HOTKEY", None)
    mode = getattr(module, "MODE", None)
    count = getattr(module, "COUNT", None)
    speed = getattr(module, "SPEED", None)
    run = getattr(module, "run", None)

    if not isinstance(name, str) or not name.strip():
        raise PythonMacroValidationError("NAME 必须是非空字符串")
    if hotkey != "f9":
        raise PythonMacroValidationError("阶段 3 的 HOTKEY 必须是 'f9'")
    if mode not in {"switch", "down"}:
        raise PythonMacroValidationError("MODE 必须是 'switch' 或 'down'")
    if not _is_int(count) or not 0 <= count <= 99:
        raise PythonMacroValidationError("COUNT 必须是 0 至 99 的整数")
    if not _is_number(speed) or not 0.01 <= float(speed) <= 8.0:
        raise PythonMacroValidationError("SPEED 必须是 0.01 至 8.0 的数字")
    if not callable(run):
        raise PythonMacroValidationError("必须定义可调用的 run(player) 函数")
    parameters = list(inspect.signature(run).parameters.values())
    if (
        len(parameters) != 1
        or parameters[0].name != "player"
        or parameters[0].default is not inspect.Parameter.empty
        or parameters[0].kind
        not in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        }
    ):
        raise PythonMacroValidationError("run 必须精确为 run(player)")
    return PythonMacro(name, hotkey, mode, count, float(speed), run)


def run_python_macro_once(
    macro: PythonMacro, stop_event: threading.Event, keybinds: GameKeybinds | None = None
) -> bool:
    """执行一轮 Python 宏；正常中断返回 False，供 SequencePlayer 停止循环。"""
    try:
        macro.run(ScriptPlayer(stop_event, macro.speed, keybinds=keybinds or load_game_keybinds()))
    except ScriptInterrupted:
        return False
    return not stop_event.is_set()


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
