"""Saved replay discovery and guarded Windows recycle-bin operations."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.core.macro_file_manager import move_path_to_windows_recycle_bin


_DATE_DIRECTORY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SESSION_DIRECTORY = re.compile(
    r"^(?P<label>.+)-(?P<date>\d{8})-(?P<time>\d{6})-recording$"
)


class ReplayHistoryError(ValueError):
    """A saved replay cannot be read or managed safely."""


@dataclass(frozen=True, slots=True)
class ReplayHistoryEntry:
    directory: Path
    display_name: str
    saved_at: datetime | None
    raw_video: Path
    metadata_path: Path
    ass_subtitle: Path
    srt_subtitle: Path
    actual_duration_ms: float | None
    quality: str
    fps: int | None
    encoder: str
    audio_track_count: int | None
    event_count: int | None
    status: str

    @property
    def subtitle_path(self) -> Path | None:
        if self.ass_subtitle.is_file():
            return self.ass_subtitle
        if self.srt_subtitle.is_file():
            return self.srt_subtitle
        return None

    @property
    def saved_at_text(self) -> str:
        if self.saved_at is not None:
            return self.saved_at.strftime("%Y-%m-%d %H:%M:%S")
        return self.directory.parent.name

    @property
    def duration_text(self) -> str:
        if self.actual_duration_ms is None:
            return "未知"
        total_seconds = max(0, round(self.actual_duration_ms / 1000))
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:d}:{seconds:02d}"

    @property
    def video_format_text(self) -> str:
        parts = [part for part in (self.quality, f"{self.fps}fps" if self.fps else "") if part]
        return " / ".join(parts) or "未知"

    @property
    def audio_text(self) -> str:
        if self.audio_track_count is None:
            return "未知"
        return f"{self.audio_track_count} 条"


class ReplayHistoryStore:
    """Read only direct date/session children below the configured capture root."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def scan(self) -> list[ReplayHistoryEntry]:
        if not self.root.is_dir():
            return []
        entries: list[ReplayHistoryEntry] = []
        try:
            date_directories = tuple(self.root.iterdir())
        except OSError:
            return []
        for date_directory in date_directories:
            if (
                date_directory.is_symlink()
                or not date_directory.is_dir()
                or not _DATE_DIRECTORY.fullmatch(date_directory.name)
            ):
                continue
            try:
                session_directories = tuple(date_directory.iterdir())
            except OSError:
                continue
            for session_directory in session_directories:
                if (
                    session_directory.name.startswith(".")
                    or session_directory.is_symlink()
                    or not session_directory.is_dir()
                ):
                    continue
                raw_video = session_directory / "raw.mp4"
                metadata_path = session_directory / "metadata.json"
                if not raw_video.is_file() and not metadata_path.is_file():
                    continue
                if not self._is_owned_session_path(session_directory):
                    continue
                entries.append(self._read_entry(session_directory))
        entries.sort(
            key=lambda entry: (
                entry.saved_at.timestamp() if entry.saved_at is not None else 0.0,
                entry.directory.name.casefold(),
            ),
            reverse=True,
        )
        return entries

    def move_to_recycle_bin(self, entry: ReplayHistoryEntry) -> None:
        target = entry.directory
        if not self._is_owned_session_path(target):
            raise ReplayHistoryError("只能删除当前视频保存目录中的录像会话")
        if target.is_symlink() or not target.is_dir():
            raise ReplayHistoryError("所选录像会话已经不存在或不是普通文件夹")
        if not (target / "raw.mp4").is_file() and not (target / "metadata.json").is_file():
            raise ReplayHistoryError("所选文件夹不再是可识别的录像会话")
        try:
            move_path_to_windows_recycle_bin(target)
        except OSError as exc:
            raise ReplayHistoryError("无法移入 Windows 回收站，录像文件仍保留") from exc

    def _is_owned_session_path(self, candidate: Path) -> bool:
        try:
            root = self.root.resolve()
            target = candidate.resolve()
            relative = target.relative_to(root)
        except (OSError, ValueError):
            return False
        return (
            len(relative.parts) == 2
            and _DATE_DIRECTORY.fullmatch(relative.parts[0]) is not None
            and target.parent.parent == root
        )

    @staticmethod
    def _read_entry(directory: Path) -> ReplayHistoryEntry:
        raw_video = directory / "raw.mp4"
        metadata_path = directory / "metadata.json"
        metadata, metadata_valid = _read_metadata(metadata_path)
        saved_at = _parse_saved_at(metadata.get("saved_at"))
        match = _SESSION_DIRECTORY.fullmatch(directory.name)
        if saved_at is None and match is not None:
            try:
                saved_at = datetime.strptime(
                    match.group("date") + match.group("time"), "%Y%m%d%H%M%S"
                )
            except ValueError:
                pass
        display_name = match.group("label") if match is not None else directory.name
        ass_subtitle = directory / "raw.ass"
        srt_subtitle = directory / "input_subtitles.srt"
        if not raw_video.is_file():
            status = "缺少原始视频"
        elif not metadata_valid:
            status = "信息不完整"
        elif not ass_subtitle.is_file() and not srt_subtitle.is_file():
            status = "外挂字幕缺失"
        else:
            status = "可播放"
        encoder_name = _first_text(
            metadata,
            "encoder_name",
            "actual_encoder_name",
            "video_encoder_name",
        )
        encoder_mode = _first_text(metadata, "encoder_mode")
        encoder = encoder_name or ({"gpu": "GPU", "cpu": "CPU"}.get(encoder_mode, encoder_mode))
        return ReplayHistoryEntry(
            directory=directory,
            display_name=display_name,
            saved_at=saved_at,
            raw_video=raw_video,
            metadata_path=metadata_path,
            ass_subtitle=ass_subtitle,
            srt_subtitle=srt_subtitle,
            actual_duration_ms=_number(metadata.get("actual_duration_ms")),
            quality=_first_text(metadata, "quality", "output_quality"),
            fps=_integer(metadata.get("requested_fps", metadata.get("fps"))),
            encoder=encoder or "未知",
            audio_track_count=_integer(metadata.get("audio_track_count")),
            event_count=_integer(metadata.get("event_count")),
            status=status,
        )


def _read_metadata(path: Path) -> tuple[dict[str, object], bool]:
    if not path.is_file():
        return {}, False
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}, False
    return (value, True) if isinstance(value, dict) else ({}, False)


def _parse_saved_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip())
    except ValueError:
        return None


def _first_text(metadata: dict[str, object], *keys: str) -> str:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _integer(value: object) -> int | None:
    number = _number(value)
    return None if number is None else int(number)
