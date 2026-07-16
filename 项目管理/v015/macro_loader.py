"""阶段 2 唯一 JSON 键盘测试宏的严格加载与校验。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.core.input_simulator import is_supported_key
from src.core.sequence_player import KeyTapStep


class MacroValidationError(ValueError):
    """JSON 存在语法或阶段 2 规格错误。"""


@dataclass(frozen=True)
class TestMacro:
    name: str
    mode: str
    count: int
    speed: float
    steps: tuple[KeyTapStep, ...]


_MACRO_FIELDS = {"name", "mode", "count", "speed", "steps"}
_STEP_FIELDS = {"type", "key", "hold_ms", "delay_ms"}
_MODES = {"switch", "down", "up"}


def load_test_macro(path: str | Path) -> TestMacro:
    """加载并严格验证阶段 2 的唯一物理键盘宏。"""
    macro_path = Path(path)
    try:
        raw = json.loads(macro_path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise MacroValidationError(f"无法读取宏文件: {macro_path}") from exc
    except json.JSONDecodeError as exc:
        raise MacroValidationError(f"宏文件不是合法 JSON: {exc.msg}") from exc

    if not isinstance(raw, dict):
        raise MacroValidationError("宏根节点必须是 JSON 对象")
    _require_exact_fields(raw, _MACRO_FIELDS, "宏")

    name = raw["name"]
    mode = raw["mode"]
    count = raw["count"]
    speed = raw["speed"]
    steps = raw["steps"]

    if not isinstance(name, str) or not name.strip():
        raise MacroValidationError("name 必须是非空字符串")
    if mode not in _MODES:
        raise MacroValidationError("mode 必须是 switch、down 或 up")
    if not _is_int(count) or not 0 <= count <= 99:
        raise MacroValidationError("count 必须是 0 至 99 的整数")
    if not _is_number(speed) or not 0.01 <= float(speed) <= 8.0:
        raise MacroValidationError("speed 必须是 0.01 至 8.0 的数字")
    if not isinstance(steps, list) or not steps:
        raise MacroValidationError("steps 必须是非空数组")

    return TestMacro(
        name=name,
        mode=mode,
        count=count,
        speed=float(speed),
        steps=tuple(_parse_step(step, index) for index, step in enumerate(steps)),
    )


def _parse_step(raw: object, index: int) -> KeyTapStep:
    if not isinstance(raw, dict):
        raise MacroValidationError(f"steps[{index}] 必须是对象")
    _require_exact_fields(raw, _STEP_FIELDS, f"steps[{index}]")
    if raw["type"] != "key_tap":
        raise MacroValidationError(f"steps[{index}].type 只能是 key_tap")
    key = raw["key"]
    if not is_supported_key(key):
        raise MacroValidationError(f"steps[{index}].key 不是受支持的物理按键")
    hold_ms = raw["hold_ms"]
    delay_ms = raw["delay_ms"]
    if not _is_int(hold_ms) or not 1 <= hold_ms <= 1000:
        raise MacroValidationError(f"steps[{index}].hold_ms 必须是 1 至 1000 的整数")
    if not _is_int(delay_ms) or not 0 <= delay_ms <= 60000:
        raise MacroValidationError(f"steps[{index}].delay_ms 必须是 0 至 60000 的整数")
    return KeyTapStep(key=key.lower(), hold_ms=hold_ms, delay_ms=delay_ms)


def _require_exact_fields(raw: dict, expected: set[str], location: str) -> None:
    actual = set(raw)
    if actual != expected:
        missing = ", ".join(sorted(expected - actual))
        unknown = ", ".join(sorted(actual - expected))
        details = []
        if missing:
            details.append(f"缺少字段: {missing}")
        if unknown:
            details.append(f"未知字段: {unknown}")
        raise MacroValidationError(f"{location} 字段不符合规格（{'；'.join(details)}）")


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
