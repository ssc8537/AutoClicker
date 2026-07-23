"""Stage 19 原生回放工作台的可移植设置。"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile

from src.utils.app_paths import capture_root, config_root


REPLAY_DURATIONS = (5, 10, 15, 30)
REPLAY_QUALITIES = ("720p", "1080p")
REPLAY_ENCODER_MODES = ("gpu", "cpu")
REPLAY_FRAME_RATES = (15, 30, 45, 60)


@dataclass(frozen=True)
class ReplaySettings:
    save_directory: Path
    duration_minutes: int = 10
    quality: str = "1080p"
    encoder_mode: str = "gpu"
    fps: int = 30
    monitor_index: int = 1
    core_path: Path | None = None
    record_microphone: bool = False
    microphone_device_id: str | None = None
    microphone_device_name: str | None = None
    microphone_gain_percent: int = 100
    desktop_gain_percent: int = 150


class ReplaySettingsStore:
    def __init__(self, path: Path | None = None, default_directory: Path | None = None):
        self.path = path or (config_root() / "replay_settings.json")
        self.default_directory = (default_directory or capture_root()).resolve()

    def load(self) -> ReplaySettings:
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            loaded = {}
        if not isinstance(loaded, dict):
            loaded = {}
        raw_directory = loaded.get("save_directory")
        directory = Path(raw_directory).expanduser() if isinstance(raw_directory, str) else self.default_directory
        if not directory.is_absolute():
            directory = self.default_directory
        duration = loaded.get("duration_minutes", 10)
        if duration not in REPLAY_DURATIONS:
            duration = 10
        quality = loaded.get("quality", "1080p")
        if quality not in REPLAY_QUALITIES:
            quality = "1080p"
        encoder_mode = loaded.get("encoder_mode", "gpu")
        if encoder_mode not in REPLAY_ENCODER_MODES:
            encoder_mode = "gpu"
        fps = loaded.get("fps", 30)
        if fps not in REPLAY_FRAME_RATES:
            fps = 30
        monitor_index = loaded.get("monitor_index", 1)
        if not isinstance(monitor_index, int) or monitor_index < 1:
            monitor_index = 1
        raw_core_path = loaded.get("core_path")
        core_path = Path(raw_core_path).expanduser().resolve() if isinstance(raw_core_path, str) else None
        if core_path is not None and not core_path.is_absolute():
            core_path = None
        record_microphone = loaded.get("record_microphone", False)
        if not isinstance(record_microphone, bool):
            record_microphone = False
        microphone_device_id = loaded.get("microphone_device_id")
        if not isinstance(microphone_device_id, str) or not microphone_device_id.strip():
            microphone_device_id = None
        microphone_device_name = loaded.get("microphone_device_name")
        if not isinstance(microphone_device_name, str) or not microphone_device_name.strip():
            microphone_device_name = None
        microphone_gain_percent = loaded.get("microphone_gain_percent", 100)
        if not isinstance(microphone_gain_percent, int) or not 0 <= microphone_gain_percent <= 200:
            microphone_gain_percent = 100
        desktop_gain_percent = loaded.get("desktop_gain_percent", 150)
        if not isinstance(desktop_gain_percent, int) or not 0 <= desktop_gain_percent <= 300:
            desktop_gain_percent = 150
        return ReplaySettings(
            directory.resolve(),
            duration,
            quality,
            encoder_mode,
            fps,
            monitor_index,
            core_path,
            record_microphone,
            microphone_device_id,
            microphone_device_name,
            microphone_gain_percent,
            desktop_gain_percent,
        )

    def save(self, settings: ReplaySettings) -> ReplaySettings:
        directory = Path(settings.save_directory).expanduser()
        if not directory.is_absolute():
            raise ValueError("视频保存目录必须是完整的绝对路径")
        if settings.duration_minutes not in REPLAY_DURATIONS:
            raise ValueError("回放时长只能是 5、10、15 或 30 分钟")
        if settings.quality not in REPLAY_QUALITIES:
            raise ValueError("清晰度只能是 720p 或 1080p")
        if settings.encoder_mode not in REPLAY_ENCODER_MODES:
            raise ValueError("编码模式只能是 GPU 或 CPU")
        if settings.fps not in REPLAY_FRAME_RATES:
            raise ValueError("录制帧率只能是 15、30、45 或 60")
        if not isinstance(settings.monitor_index, int) or settings.monitor_index < 1:
            raise ValueError("显示器编号必须从 1 开始")
        core_path = None
        if settings.core_path is not None:
            core_path = Path(settings.core_path).expanduser()
            if not core_path.is_absolute():
                raise ValueError("录像核心必须使用完整绝对路径")
            core_path = core_path.resolve()
        validated = ReplaySettings(
            directory.resolve(),
            settings.duration_minutes,
            settings.quality,
            settings.encoder_mode,
            settings.fps,
            settings.monitor_index,
            core_path,
            bool(settings.record_microphone),
            settings.microphone_device_id.strip()
            if isinstance(settings.microphone_device_id, str)
            and settings.microphone_device_id.strip()
            else None,
            settings.microphone_device_name.strip()
            if isinstance(settings.microphone_device_name, str)
            and settings.microphone_device_name.strip()
            else None,
            int(settings.microphone_gain_percent),
            int(settings.desktop_gain_percent),
        )
        if not 0 <= validated.microphone_gain_percent <= 200:
            raise ValueError("麦克风音量只能是 0% 到 200%")
        if not 0 <= validated.desktop_gain_percent <= 300:
            raise ValueError("桌面声音音量只能是 0% 到 300%")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_name: str | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self.path.name}.", dir=self.path.parent, text=True
            )
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as temporary:
                json.dump(
                    {
                        "save_directory": str(validated.save_directory),
                        "duration_minutes": validated.duration_minutes,
                        "quality": validated.quality,
                        "encoder_mode": validated.encoder_mode,
                        "fps": validated.fps,
                        "monitor_index": validated.monitor_index,
                        "core_path": str(validated.core_path) if validated.core_path else None,
                        "record_microphone": validated.record_microphone,
                        "microphone_device_id": validated.microphone_device_id,
                        "microphone_device_name": validated.microphone_device_name,
                        "microphone_gain_percent": validated.microphone_gain_percent,
                        "desktop_gain_percent": validated.desktop_gain_percent,
                    },
                    temporary,
                    ensure_ascii=False,
                    indent=2,
                )
                temporary.write("\n")
            os.replace(temporary_name, self.path)
        finally:
            if temporary_name is not None and Path(temporary_name).exists():
                Path(temporary_name).unlink(missing_ok=True)
        return validated
