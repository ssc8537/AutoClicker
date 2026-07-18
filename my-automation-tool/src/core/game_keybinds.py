"""Stage 3K 的共享游戏键位配置：校验、读取和原子保存。"""
from __future__ import annotations

import configparser
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from src.utils.app_paths import config_root
from types import MappingProxyType
from typing import Mapping

from src.core.input_simulator import is_supported_key


class GameKeybindError(ValueError):
    """键位配置无法安全使用或保存。"""


KEYBIND_FIELDS = (
    ("character_1", "角色 1", "1"),
    ("character_2", "角色 2", "2"),
    ("character_3", "角色 3", "3"),
    ("skill", "战技", "E"),
    ("echo", "声骸", "Q"),
    ("ultimate", "大招", "R"),
    ("jump", "跳跃", "Space"),
    ("execute", "处决", "F"),
)
KEYBIND_NAMES = tuple(field[0] for field in KEYBIND_FIELDS)
RESERVED_KEYS = frozenset({"f2", "f9", "f12"})


def default_config_path() -> Path:
    return config_root() / "game_keybinds.ini"


def _normalise_key(value: object) -> str:
    if not isinstance(value, str):
        raise GameKeybindError("键位必须是文本")
    key = value.strip().lower()
    if not key or not is_supported_key(key):
        raise GameKeybindError(f"不支持的物理键：{value!r}")
    if key in RESERVED_KEYS:
        raise GameKeybindError(f"键位 {key.upper()} 是程序保留键")
    return key


def display_key(key: str) -> str:
    """为 INI 和设置页提供稳定、易读的物理键显示。"""
    return "Space" if key == "space" else key.upper()


@dataclass(frozen=True)
class GameKeybinds:
    """所有可信 Python 宏共享的八个键盘物理键。"""

    values: Mapping[str, str]

    def __post_init__(self) -> None:
        provided = set(self.values)
        expected = set(KEYBIND_NAMES)
        if provided != expected:
            missing = expected - provided
            extra = provided - expected
            raise GameKeybindError(f"键位字段不完整：缺少 {sorted(missing)}，多出 {sorted(extra)}")
        normalised = {name: _normalise_key(value) for name, value in self.values.items()}
        if len(set(normalised.values())) != len(normalised):
            raise GameKeybindError("各游戏动作不能使用重复键位")
        object.__setattr__(self, "values", MappingProxyType(normalised))

    def key_for(self, name: str) -> str:
        try:
            return self.values[name]
        except KeyError as exc:
            raise GameKeybindError(f"未知游戏动作：{name}") from exc


DEFAULT_GAME_KEYBINDS = GameKeybinds({name: default for name, _, default in KEYBIND_FIELDS})


def load_game_keybinds(path: Path | None = None) -> GameKeybinds:
    """读取配置；首次缺失时返回默认值，但不在读取时写盘。"""
    config_path = path or default_config_path()
    if not config_path.exists():
        return DEFAULT_GAME_KEYBINDS
    parser = configparser.ConfigParser(interpolation=None)
    try:
        with config_path.open("r", encoding="utf-8") as stream:
            parser.read_file(stream)
    except (OSError, UnicodeError, configparser.Error) as exc:
        raise GameKeybindError(f"无法读取键位配置：{exc}") from exc
    if set(parser.sections()) != {"game_keybinds"}:
        raise GameKeybindError("键位配置必须只包含 [game_keybinds] 段")
    section = parser["game_keybinds"]
    if set(section) != set(KEYBIND_NAMES):
        raise GameKeybindError("键位配置字段不完整或包含未知字段")
    return GameKeybinds(dict(section))


def save_game_keybinds(keybinds: GameKeybinds, path: Path | None = None) -> None:
    """校验后原子替换 INI；失败时旧的有效文件不受影响。"""
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    parser = configparser.ConfigParser(interpolation=None)
    parser["game_keybinds"] = {
        name: display_key(keybinds.key_for(name)) for name in KEYBIND_NAMES
    }
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", delete=False,
            dir=config_path.parent, prefix=f".{config_path.name}.", suffix=".tmp",
        ) as stream:
            parser.write(stream)
            stream.flush()
            os.fsync(stream.fileno())
            temporary_path = Path(stream.name)
        os.replace(temporary_path, config_path)
    except OSError as exc:
        raise GameKeybindError(f"键位保存失败，旧配置未改变：{exc}") from exc
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)
