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

from src.core.input_keys import display_input_key, normalise_input_key


class GameKeybindError(ValueError):
    """键位配置无法安全使用或保存。"""


CORE_KEYBIND_FIELDS = (
    ("character_1", "角色 1", "1"),
    ("character_2", "角色 2", "2"),
    ("character_3", "角色 3", "3"),
    ("skill", "战技", "E"),
    ("echo", "声骸", "Q"),
    ("ultimate", "大招", "R"),
    ("jump", "跳跃", "Space"),
    ("execute", "处决", "F"),
)
EXTENSION_KEYBIND_FIELDS = (
    ("extension_1", "扩展键 1", "F13"),
    ("extension_2", "扩展键 2", "F14"),
    ("extension_3", "扩展键 3", "F15"),
)
KEYBIND_FIELDS = CORE_KEYBIND_FIELDS + EXTENSION_KEYBIND_FIELDS
KEYBIND_NAMES = tuple(field[0] for field in KEYBIND_FIELDS)
CORE_KEYBIND_NAMES = tuple(field[0] for field in CORE_KEYBIND_FIELDS)
EXTENSION_KEYBIND_NAMES = tuple(field[0] for field in EXTENSION_KEYBIND_FIELDS)
DEFAULT_KEYBIND_LABELS = {name: label for name, label, _ in KEYBIND_FIELDS}
DEFAULT_KEYBIND_VALUES = {name: default for name, _, default in KEYBIND_FIELDS}


def default_config_path() -> Path:
    return config_root() / "game_keybinds.ini"


def _normalise_key(value: object) -> str:
    if not isinstance(value, str):
        raise GameKeybindError("键位必须是文本")
    try:
        return normalise_input_key(value)
    except ValueError as exc:
        raise GameKeybindError(str(exc)) from exc


def display_key(key: str) -> str:
    """为 INI 和设置页提供稳定、易读的物理键显示。"""
    return display_input_key(key)


@dataclass(frozen=True)
class GameKeybinds:
    """All eight shared physical keys and their player-editable labels."""

    values: Mapping[str, str]
    labels: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        supplied_values = set(self.values)
        values_source = (
            {**DEFAULT_KEYBIND_VALUES, **self.values}
            if supplied_values == set(CORE_KEYBIND_NAMES)
            else self.values
        )
        provided = set(values_source)
        expected = set(KEYBIND_NAMES)
        if provided != expected:
            missing = expected - provided
            extra = provided - expected
            raise GameKeybindError(f"键位字段不完整：缺少 {sorted(missing)}，多出 {sorted(extra)}")
        normalised = {name: _normalise_key(value) for name, value in values_source.items()}
        supplied_labels = self.labels or {}
        raw_labels = {**DEFAULT_KEYBIND_LABELS, **supplied_labels}
        if set(raw_labels) != expected:
            raise GameKeybindError("动作名称字段不完整或包含未知字段")
        labels = {}
        for name, value in raw_labels.items():
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > 24:
                raise GameKeybindError("每个动作名称必须是 1 至 24 个文字")
            labels[name] = value.strip()
        if len(set(labels.values())) != len(labels):
            raise GameKeybindError("动作名称不能重复，请用“大招 1”“大招 2”区分")
        object.__setattr__(self, "values", MappingProxyType(normalised))
        object.__setattr__(self, "labels", MappingProxyType(labels))

    def key_for(self, name: str) -> str:
        try:
            return self.values[name]
        except KeyError as exc:
            raise GameKeybindError(f"未知游戏动作：{name}") from exc

    def label_for(self, name: str) -> str:
        try:
            return self.labels[name]
        except KeyError as exc:
            raise GameKeybindError(f"未知游戏动作：{name}") from exc

    def key_for_label(self, label: str) -> str:
        if not isinstance(label, str):
            raise GameKeybindError("动作名称必须是文本")
        name = next((name for name, value in self.labels.items() if value == label.strip()), None)
        if name is None:
            raise GameKeybindError(f"找不到动作名称：{label}")
        return self.key_for(name)


DEFAULT_GAME_KEYBINDS = GameKeybinds(DEFAULT_KEYBIND_VALUES)


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
    sections = set(parser.sections())
    if sections not in ({"game_keybinds"}, {"game_keybinds", "game_keybind_labels"}):
        raise GameKeybindError("键位配置段无效")
    section = parser["game_keybinds"]
    if set(section) not in (set(CORE_KEYBIND_NAMES), set(KEYBIND_NAMES)):
        raise GameKeybindError("键位配置字段不完整或包含未知字段")
    labels = (
        dict(parser["game_keybind_labels"])
        if "game_keybind_labels" in parser
        else {}
    )
    return GameKeybinds(dict(section), labels)


def save_game_keybinds(keybinds: GameKeybinds, path: Path | None = None) -> None:
    """校验后原子替换 INI；失败时旧的有效文件不受影响。"""
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    parser = configparser.ConfigParser(interpolation=None)
    parser["game_keybinds"] = {
        name: keybinds.key_for(name) for name in KEYBIND_NAMES
    }
    parser["game_keybind_labels"] = {
        name: keybinds.label_for(name) for name in KEYBIND_NAMES
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
