"""Atomic persistence for the one configurable global start/stop key."""
from __future__ import annotations

import configparser
import os
import tempfile
from pathlib import Path

from src.core.input_keys import normalise_input_key
from src.utils.app_paths import config_root

DEFAULT_GLOBAL_HOTKEY = "backquote"


class GlobalHotkeyError(ValueError):
    """The global key cannot be loaded or saved safely."""


def default_config_path() -> Path:
    return config_root() / "global_hotkey.ini"


def load_global_hotkey(path: Path | None = None) -> str:
    config_path = path or default_config_path()
    if not config_path.exists():
        return DEFAULT_GLOBAL_HOTKEY
    parser = configparser.ConfigParser(interpolation=None)
    try:
        with config_path.open("r", encoding="utf-8") as stream:
            parser.read_file(stream)
    except (OSError, UnicodeError, configparser.Error) as exc:
        raise GlobalHotkeyError(f"无法读取全局键设置：{exc}") from exc
    if set(parser.sections()) != {"global_hotkey"} or set(parser["global_hotkey"]) != {"key"}:
        raise GlobalHotkeyError("全局键设置格式无效")
    try:
        return normalise_input_key(parser["global_hotkey"]["key"])
    except ValueError as exc:
        raise GlobalHotkeyError(str(exc)) from exc


def save_global_hotkey(key: str, path: Path | None = None) -> str:
    try:
        canonical = normalise_input_key(key)
    except ValueError as exc:
        raise GlobalHotkeyError(str(exc)) from exc
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    parser = configparser.ConfigParser(interpolation=None)
    parser["global_hotkey"] = {"key": canonical}
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
        raise GlobalHotkeyError(f"全局键保存失败，旧设置未改变：{exc}") from exc
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)
    return canonical
