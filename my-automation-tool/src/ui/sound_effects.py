"""默认开启、非阻塞的本地提示音；绝不影响宏停止和释放。"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Callable

from src.utils.app_paths import config_root, resource_root
from src.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import winsound
except ImportError:  # pragma: no cover - Windows 便携版外的静默回退
    winsound = None


class SoundEffects:
    """为全局启停和首次选中窗口提供两种自制 WAV 提示。"""

    _SETTING_KEY = "sound_effects_enabled"
    _DEFAULT_ON_VERSION_KEY = "sound_effects_default_on_v2"

    def __init__(
        self,
        *,
        settings_path: Path | None = None,
        assets_root: Path | None = None,
        play_sound: Callable[[str, int], object] | None = None,
    ):
        self._settings_path = settings_path or (config_root() / "settings.json")
        self._assets_root = assets_root or (resource_root() / "assets")
        if play_sound is not None:
            self._play_sound = play_sound
        elif os.environ.get("MYAUTOPLAYER_DISABLE_AUDIO") == "1":
            self._play_sound = None
        else:
            self._play_sound = winsound.PlaySound if winsound is not None else None
        self._flags = (
            winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
            if winsound is not None
            else 0
        )
        self.enabled = self._load_enabled()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)
        self._save_enabled()

    def play_started(self) -> None:
        self._play("sound-on.wav", "global-enabled")

    def play_stopped(self) -> None:
        self._play("sound-off.wav", "global-disabled")

    def play_selected(self) -> None:
        self._play("sound-on.wav", "focus-selected")

    def _play(self, filename: str, source: str) -> None:
        path = self._assets_root / filename
        if not self.enabled or self._play_sound is None or not path.is_file():
            return
        try:
            logger.info("播放提示音：%s，来源=%s", filename, source)
            self._play_sound(str(path), self._flags)
        except Exception:
            pass

    def _load_enabled(self) -> bool:
        try:
            data = json.loads(self._settings_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return True
            # Before Stage 7C a missing marker meant the old global default was
            # off. Treat those old files as the new default on, but never undo a
            # choice made after this migration.
            if not data.get(self._DEFAULT_ON_VERSION_KEY, False):
                return True
            return bool(data.get(self._SETTING_KEY, True))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return True

    def _save_enabled(self) -> None:
        temporary_name = None
        try:
            data = {}
            if self._settings_path.is_file():
                loaded = json.loads(self._settings_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data = loaded
            data[self._SETTING_KEY] = self.enabled
            data[self._DEFAULT_ON_VERSION_KEY] = True
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self._settings_path.name}.", dir=self._settings_path.parent, text=True
            )
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as temporary:
                json.dump(data, temporary, ensure_ascii=False, indent=2)
                temporary.write("\n")
            os.replace(temporary_name, self._settings_path)
        except (OSError, UnicodeError, json.JSONDecodeError):
            if temporary_name is not None:
                Path(temporary_name).unlink(missing_ok=True)
