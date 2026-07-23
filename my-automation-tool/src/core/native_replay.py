"""Stage 19 native rolling replay buffer and input-timeline boundary."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import csv
import ctypes
from ctypes import wintypes
import json
import math
import os
from pathlib import Path
import queue
import shutil
import subprocess
import tempfile
import threading
import time

from src.core.game_keybinds import KEYBIND_NAMES, load_game_keybinds
from src.core.hotkey_manager import PhysicalInputEvent
from src.core.input_keys import physical_event_text, physical_input_name
from src.core.input_subtitles import write_input_subtitles
from src.core.replay_settings import ReplaySettings
from src.utils.app_paths import application_root, resource_root


QUALITY_DIMENSIONS = {
    "720p": (1280, 720, 6_000_000),
    "1080p": (1920, 1080, 12_000_000),
}
SEGMENT_SECONDS = 10
QPC_TICKS_PER_SECOND = 10_000_000
_INVALID_SESSION_NAME_CHARS = set('<>:"/\\|?*')
_RESERVED_WINDOWS_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
_CSV_HEADER = [
    "序号", "本地时间", "相对毫秒", "距上一事件毫秒", "按键事件",
    "物理键命名", "项目键值", "中文动作", "按下持续毫秒", "松开间隔毫秒",
    "事件后仍按住", "重叠按键", "前台进程", "前台PID",
]


@dataclass(frozen=True)
class NativeReplayBuffer:
    directory: Path
    segments_directory: Path
    manifest: Path
    audio_manifest: Path
    audio_levels: Path
    audio_info: Path
    metadata: Path
    native_log: Path
    events_jsonl: Path
    events_csv: Path
    stop_file: Path
    rotate_file: Path
    rotate_ack: Path


@dataclass(frozen=True)
class NativeReplaySession:
    directory: Path
    raw_video: Path
    metadata: Path
    native_log: Path
    events_jsonl: Path
    events_csv: Path
    input_subtitles: Path
    preview_subtitles: Path


@dataclass(frozen=True)
class _WriterBarrier:
    completed: threading.Event


def native_replay_executable(custom_path: Path | None = None) -> Path | None:
    if custom_path is not None:
        selected = Path(custom_path).expanduser()
        if selected.is_file() and selected.suffix.casefold() == ".exe":
            return selected.resolve()
    candidates = (
        application_root() / "native-replay" / "myautoplayer-native-replay.exe",
        resource_root() / "native-replay" / "myautoplayer-native-replay.exe",
        application_root() / "native-replay" / "target" / "release" / "myautoplayer-native-replay.exe",
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def normalise_replay_session_name(value: object) -> str:
    """Validate one user-facing Windows folder label without changing its meaning."""
    if not isinstance(value, str):
        raise ValueError("录像文件夹名称必须是文字")
    name = value.strip().rstrip(". ")
    if not name:
        raise ValueError("请填写录像文件夹名称")
    if len(name) > 60:
        raise ValueError("录像文件夹名称最多60个字符")
    if any(character in _INVALID_SESSION_NAME_CHARS or ord(character) < 32 for character in name):
        raise ValueError('名称不能包含 < > : " / \\ | ? *')
    if name.split(".", 1)[0].upper() in _RESERVED_WINDOWS_NAMES:
        raise ValueError("这个名称被 Windows 保留，请换一个名称")
    return name


def _write_merge_plan(
    path: Path,
    output: Path,
    video_segments: list[Path],
    desktop_segments: list[Path],
    microphone_segments: list[Path],
) -> None:
    """Write an unbounded segment list while the process command stays constant-size."""
    lines = [f"output\t{output}"]
    lines.extend(f"video\t{segment}" for segment in video_segments)
    lines.extend(f"desktop\t{segment}" for segment in desktop_segments)
    lines.extend(f"microphone\t{segment}" for segment in microphone_segments)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


class NativeReplayController:
    """Own one native rolling buffer and export immutable recent snapshots."""

    def __init__(self) -> None:
        self._process: subprocess.Popen | None = None
        self._buffer: NativeReplayBuffer | None = None
        self._session: NativeReplaySession | None = None
        self._capture_settings: ReplaySettings | None = None
        self._log_stream = None
        self._lock = threading.RLock()
        self._save_lock = threading.Lock()
        self._input_queue: queue.Queue[PhysicalInputEvent | _WriterBarrier | None] = queue.Queue(maxsize=4096)
        self._input_thread: threading.Thread | None = None
        self._input_dropped = 0
        self._session_monotonic_ns = 0
        self._session_wall_ns = 0

    @property
    def available(self) -> bool:
        return native_replay_executable() is not None

    def executable_for(self, settings: ReplaySettings) -> Path | None:
        return native_replay_executable(settings.core_path)

    @property
    def running(self) -> bool:
        with self._lock:
            return self._process is not None and self._process.poll() is None

    @property
    def session(self) -> NativeReplaySession | None:
        return self._session

    @property
    def buffer(self) -> NativeReplayBuffer | None:
        return self._buffer

    def start(self, settings: ReplaySettings, *, duration_seconds: int = 86_400) -> NativeReplayBuffer:
        with self._lock:
            if self.running:
                raise RuntimeError("原生录像已经在运行")
            # A previous failed/stopped capture may still be available for diagnostics.
            # Once the user starts again it is no longer useful and must not accumulate.
            self.cleanup_buffer()
            executable = self.executable_for(settings)
            if executable is None:
                raise RuntimeError("没有找到录像核心，请点击“选择录像核心”并选择 myautoplayer-native-replay.exe")
            now = datetime.now()
            buffer_dir = (
                settings.save_directory
                / ".replay-buffer"
                / f"{now:%Y%m%d-%H%M%S}-{os.getpid()}-{time.time_ns() % 1_000_000:06d}"
            )
            segments = buffer_dir / "segments"
            segments.mkdir(parents=True, exist_ok=False)
            buffer = NativeReplayBuffer(
                buffer_dir,
                segments,
                buffer_dir / "segments.jsonl",
                buffer_dir / "audio-segments.jsonl",
                buffer_dir / "audio-levels.json",
                buffer_dir / "audio-info.json",
                buffer_dir / "buffer-metadata.json",
                buffer_dir / "native.log",
                buffer_dir / "events.jsonl",
                buffer_dir / "events.csv",
                buffer_dir / ".stop",
                buffer_dir / ".rotate",
                buffer_dir / ".rotate-ack",
            )
            width, height, bitrate = QUALITY_DIMENSIONS[settings.quality]
            max_segments = math.ceil((30 * 60 + 30) / SEGMENT_SECONDS) + 2
            command = [
                str(executable),
                "--monitor", str(settings.monitor_index),
                "--duration", str(max(60, int(duration_seconds))),
                "--width", str(width),
                "--height", str(height),
                "--fps", str(settings.fps),
                "--bitrate", str(bitrate),
                "--encoder", settings.encoder_mode,
                "--metadata", str(buffer.metadata),
                "--stop-file", str(buffer.stop_file),
                "--segment-directory", str(buffer.segments_directory),
                "--manifest", str(buffer.manifest),
                "--audio-manifest", str(buffer.audio_manifest),
                "--audio-levels", str(buffer.audio_levels),
                "--audio-info", str(buffer.audio_info),
                "--record-microphone", str(settings.record_microphone).lower(),
                "--microphone-device-id", _wasapi_endpoint_id(settings.microphone_device_id),
                "--microphone-gain-percent", str(settings.microphone_gain_percent),
                "--desktop-gain-percent", str(settings.desktop_gain_percent),
                "--rotate-file", str(buffer.rotate_file),
                "--rotate-ack", str(buffer.rotate_ack),
                "--segment-seconds", str(SEGMENT_SECONDS),
                "--max-segments", str(max_segments),
            ]
            self._log_stream = buffer.native_log.open("w", encoding="utf-8", newline="\n")
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            try:
                self._process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=self._log_stream,
                    stderr=subprocess.STDOUT,
                    creationflags=creation_flags,
                    close_fds=True,
                )
            except Exception:
                self._log_stream.close()
                self._log_stream = None
                raise
            self._buffer = buffer
            self._session = None
            self._capture_settings = settings
            self._input_queue = queue.Queue(maxsize=4096)
            self._start_input_writer_locked(buffer)
            return buffer

    def audio_levels(self) -> tuple[int, int]:
        """Return the latest real PCM peaks as desktop/microphone percentages."""
        buffer = self._buffer
        if buffer is None:
            return 0, 0
        payload = self._read_json_object(buffer.audio_levels)
        try:
            desktop = max(0, min(100, int(payload.get("desktop", 0))))
            microphone = max(0, min(100, int(payload.get("microphone", 0))))
        except (TypeError, ValueError):
            return 0, 0
        return desktop, microphone

    def poll(self) -> int | None:
        with self._lock:
            if self._process is None:
                return None
            return_code = self._process.poll()
            if return_code is not None:
                self._close_log_locked()
                self._stop_input_writer_locked()
            return return_code

    def stop(self, timeout: float = 15.0) -> int | None:
        with self._lock:
            process = self._process
            buffer = self._buffer
            if process is None:
                return None
            if process.poll() is None and buffer is not None:
                buffer.stop_file.touch()
        try:
            return_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                return_code = process.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                process.kill()
                return_code = process.wait(timeout=2.0)
        with self._lock:
            self._close_log_locked()
            self._stop_input_writer_locked()
        return return_code

    def request_stop(self) -> None:
        with self._lock:
            if self._process is not None and self._process.poll() is None and self._buffer is not None:
                self._buffer.stop_file.touch()

    def save_recent(
        self,
        settings: ReplaySettings,
        label: str,
        *,
        duration_minutes: int | None = None,
        timeout: float = 30.0,
    ) -> NativeReplaySession:
        """Freeze and export one recent window without stopping an active buffer."""
        safe_label = normalise_replay_session_name(label)
        if not self._save_lock.acquire(blocking=False):
            raise RuntimeError("已有一份“保留过往”正在生成，请等待完成")
        try:
            buffer = self._buffer
            if buffer is None or not buffer.directory.is_dir():
                raise RuntimeError("当前没有可保存的回放缓冲")
            capture_settings = self._capture_settings or settings
            executable = self.executable_for(capture_settings)
            if executable is None:
                raise RuntimeError("录像核心已不存在，无法合并回放分段")

            end_index = None
            if self.running:
                end_index = self._force_rotate(buffer, timeout=timeout)
            else:
                self.poll()
            self._flush_input_writer(timeout=3.0)
            manifest = self._wait_for_manifest_index(buffer, end_index, timeout=timeout)
            if not manifest:
                raise RuntimeError("回放缓冲还没有完成可播放的录像分段")
            if end_index is None:
                end_index = max(item["index"] for item in manifest)
            available = [
                item for item in manifest
                if item["index"] <= end_index
                and (buffer.segments_directory / item["file"]).is_file()
            ]
            if not available:
                raise RuntimeError("所选时间窗内没有可用的录像分段")
            available.sort(key=lambda item: item["index"])
            end_qpc = available[-1]["end_qpc"]
            minutes = int(duration_minutes or capture_settings.duration_minutes)
            requested_ticks = max(1, minutes) * 60 * QPC_TICKS_PER_SECOND
            requested_start_qpc = end_qpc - requested_ticks
            selected = [item for item in available if item["end_qpc"] >= requested_start_qpc]
            actual_start_qpc = selected[0]["start_qpc"]
            actual_duration_ms = max(0.0, (end_qpc - actual_start_qpc) / 10_000)
            selected_indices = [int(item["index"]) for item in selected]
            audio_manifest = self._wait_for_audio_manifest_indices(
                buffer,
                selected_indices,
                microphone_enabled=capture_settings.record_microphone,
                timeout=timeout,
            )
            desktop_audio = self._select_audio_segments(audio_manifest, "desktop", selected_indices)
            microphone_audio = (
                self._select_audio_segments(audio_manifest, "microphone", selected_indices)
                if capture_settings.record_microphone
                else []
            )
            audio_sync_error_ms = self._validate_audio_boundaries(
                selected,
                desktop_audio,
                microphone_audio,
            )

            now = datetime.now()
            date_dir = capture_settings.save_directory / now.strftime("%Y-%m-%d")
            date_dir.mkdir(parents=True, exist_ok=True)
            target = date_dir / f"{safe_label}-{now:%Y%m%d-%H%M%S}-recording"
            if target.exists():
                raise FileExistsError(f"录像文件夹已存在：{target.name}")
            temporary = date_dir / f".{target.name}.saving"
            if temporary.exists():
                raise FileExistsError(f"临时保存目录已存在：{temporary.name}")
            temporary.mkdir()
            session = NativeReplaySession(
                temporary,
                temporary / "raw.mp4",
                temporary / "metadata.json",
                temporary / "native.log",
                temporary / "events.jsonl",
                temporary / "events.csv",
                temporary / "raw.ass",
                temporary / "input_subtitles.srt",
            )
            try:
                pinned_dir = temporary / ".segments"
                pinned_dir.mkdir()
                pinned_segments = []
                for item in selected:
                    source = buffer.segments_directory / item["file"]
                    pinned = pinned_dir / item["file"]
                    try:
                        os.link(source, pinned)
                    except OSError:
                        shutil.copy2(source, pinned)
                    pinned_segments.append(pinned)
                pinned_desktop = self._pin_audio_segments(
                    buffer, pinned_dir, desktop_audio
                )
                pinned_microphone = self._pin_audio_segments(
                    buffer, pinned_dir, microphone_audio
                )
                # Windows CreateProcess has a finite command-line length. A 30-minute
                # save can contain hundreds of paths, so pass one compact UTF-8 plan.
                merge_plan = pinned_dir / "merge-plan.txt"
                _write_merge_plan(
                    merge_plan,
                    session.raw_video,
                    pinned_segments,
                    pinned_desktop,
                    pinned_microphone,
                )
                merge_command = [str(executable), "--merge-manifest", str(merge_plan)]
                creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                completed = subprocess.run(
                    merge_command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=creation_flags,
                    close_fds=True,
                    timeout=max(timeout, 30.0),
                    check=False,
                )
                buffer_log = buffer.native_log.read_text(encoding="utf-8", errors="replace") if buffer.native_log.is_file() else ""
                session.native_log.write_text(
                    buffer_log + "\n--- 保存合并 ---\n" + completed.stdout,
                    encoding="utf-8",
                    newline="\n",
                )
                if completed.returncode != 0 or not session.raw_video.is_file():
                    raise RuntimeError(f"回放分段合并失败（退出码 {completed.returncode}），请查看 native.log")
                shutil.rmtree(pinned_dir)

                start_ns = actual_start_qpc * 100
                end_ns = end_qpc * 100
                records = self._read_window_records(buffer.events_jsonl, start_ns, end_ns)
                self._write_session_events(session, records, start_ns)
                subtitle_count = write_input_subtitles(
                    session.input_subtitles,
                    records,
                    session_end_ms=actual_duration_ms,
                    srt_target=session.preview_subtitles,
                )
                metadata = self._read_json_object(buffer.metadata)
                audio_info = self._read_json_object(buffer.audio_info)
                audio_status = self._read_json_object(buffer.audio_levels)
                metadata.update({
                    "schema": 3,
                    "mode": "saved_recent_replay",
                    "requested_duration_minutes": minutes,
                    "requested_duration_ms": minutes * 60_000,
                    "actual_duration_ms": round(actual_duration_ms, 3),
                    "actual_extra_before_requested_ms": round(max(0.0, actual_duration_ms - minutes * 60_000), 3),
                    "segment_seconds": SEGMENT_SECONDS,
                    "segment_count": len(selected),
                    "first_segment_index": selected[0]["index"],
                    "last_segment_index": selected[-1]["index"],
                    "start_qpc_100ns": actual_start_qpc,
                    "end_qpc_100ns": end_qpc,
                    "event_count": len(records),
                    "input_dropped": self._input_dropped,
                    "input_subtitles": session.input_subtitles.name,
                    "preview_subtitles": session.preview_subtitles.name,
                    "subtitle_count": subtitle_count,
                    "video_delivery": "raw_video_with_external_subtitles",
                    "audio_track_count": 2 if capture_settings.record_microphone else 1,
                    "container_track_count": 3 if capture_settings.record_microphone else 2,
                    "desktop_audio_track_ordinal": 1,
                    "desktop_audio_track_id": 2,
                    "microphone_audio_track_ordinal": 2 if capture_settings.record_microphone else None,
                    "microphone_audio_track_id": 3 if capture_settings.record_microphone else None,
                    "desktop_gain_percent": capture_settings.desktop_gain_percent,
                    "microphone_gain_percent": capture_settings.microphone_gain_percent,
                    "audio_format": "AAC 48kHz stereo",
                    "audio_sample_rate_hz": 48_000,
                    "audio_channels": 2,
                    "audio_pcm_bits_per_sample": 16,
                    "audio_bitrate_bps_per_track": 192_000,
                    "audio_sync_error_ms": round(audio_sync_error_ms, 3),
                    "desktop_audio_device_id": audio_info.get("desktop_device_id"),
                    "desktop_audio_device_name": audio_info.get("desktop_device_name"),
                    "microphone_enabled": capture_settings.record_microphone,
                    "microphone_device_id": audio_info.get("microphone_device_id"),
                    "microphone_device_name": audio_info.get("microphone_device_name"),
                    "microphone_gain_percent": capture_settings.microphone_gain_percent,
                    "desktop_audio_discontinuities_recovered": int(
                        audio_status.get("desktop_discontinuities", 0) or 0
                    ),
                    "microphone_audio_discontinuities_recovered": int(
                        audio_status.get("microphone_discontinuities", 0) or 0
                    ),
                    "quality": capture_settings.quality,
                    "requested_fps": capture_settings.fps,
                    "encoder_mode": capture_settings.encoder_mode,
                    "monitor_index": capture_settings.monitor_index,
                    "saved_at": now.isoformat(timespec="milliseconds"),
                })
                session.metadata.write_text(
                    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
                temporary.rename(target)
            except Exception:
                if temporary.is_dir():
                    shutil.rmtree(temporary, ignore_errors=True)
                raise
            saved = NativeReplaySession(
                target,
                target / "raw.mp4",
                target / "metadata.json",
                target / "native.log",
                target / "events.jsonl",
                target / "events.csv",
                target / "raw.ass",
                target / "input_subtitles.srt",
            )
            self._session = saved
            return saved
        finally:
            self._save_lock.release()

    def observe_input(self, event: PhysicalInputEvent) -> None:
        """Hook-safe observer: one bounded nonblocking enqueue, nothing else."""
        if not self.running:
            return
        try:
            self._input_queue.put_nowait(event)
        except queue.Full:
            self._input_dropped += 1

    def cleanup_buffer(self) -> None:
        """Delete only this controller's stopped temporary buffer."""
        with self._lock:
            if self.running or self._save_lock.locked():
                return
            buffer = self._buffer
            if buffer is None:
                return
            resolved = buffer.directory.resolve()
            if resolved.parent.name != ".replay-buffer":
                raise RuntimeError("拒绝清理未知的回放缓存路径")
            shutil.rmtree(resolved, ignore_errors=True)
            self._buffer = None
            self._capture_settings = None

    def _force_rotate(self, buffer: NativeReplayBuffer, *, timeout: float) -> int:
        for marker in (buffer.rotate_ack, buffer.rotate_file):
            try:
                marker.unlink()
            except FileNotFoundError:
                pass
        buffer.rotate_file.touch()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if buffer.rotate_ack.is_file():
                try:
                    return int(buffer.rotate_ack.read_text(encoding="ascii").strip())
                except (OSError, ValueError):
                    pass
            if not self.running:
                raise RuntimeError("录像核心在封闭当前回放分段前意外退出")
            time.sleep(0.05)
        raise TimeoutError("等待录像核心封闭当前分段超时；缓冲仍在运行，可稍后重试")

    def _wait_for_manifest_index(
        self,
        buffer: NativeReplayBuffer,
        index: int | None,
        *,
        timeout: float,
    ) -> list[dict[str, int | str]]:
        deadline = time.monotonic() + timeout
        while True:
            items = self._load_manifest(buffer.manifest)
            if index is None or any(item["index"] == index for item in items):
                return items
            if time.monotonic() >= deadline:
                raise TimeoutError("等待录像分段完成 MP4 封装超时；缓冲仍在运行，可稍后重试")
            time.sleep(0.05)

    def _wait_for_audio_manifest_indices(
        self,
        buffer: NativeReplayBuffer,
        indices: list[int],
        *,
        microphone_enabled: bool,
        timeout: float,
    ) -> list[dict[str, int | str]]:
        required = {("desktop", index) for index in indices}
        if microphone_enabled:
            required.update(("microphone", index) for index in indices)
        deadline = time.monotonic() + timeout
        while True:
            items = self._load_manifest(buffer.audio_manifest)
            available = {
                (str(item.get("source", "")), int(item["index"]))
                for item in items
                if (buffer.segments_directory / str(item["file"])).is_file()
            }
            if required.issubset(available):
                return items
            if time.monotonic() >= deadline:
                missing = len(required - available)
                raise TimeoutError(f"等待音频分段完成 AAC 编码超时（还缺 {missing} 段）")
            if not self.running and self.poll() not in (None, 0):
                raise RuntimeError("录像核心在完成音频分段前意外退出")
            time.sleep(0.05)

    @staticmethod
    def _select_audio_segments(
        manifest: list[dict[str, int | str]],
        source: str,
        indices: list[int],
    ) -> list[dict[str, int | str]]:
        by_index = {
            int(item["index"]): item
            for item in manifest
            if item.get("source") == source
        }
        missing = [index for index in indices if index not in by_index]
        if missing:
            raise RuntimeError(f"{source} 音频分段缺失：{missing[0]}")
        return [by_index[index] for index in indices]

    @staticmethod
    def _validate_audio_boundaries(
        video: list[dict[str, int | str]],
        desktop: list[dict[str, int | str]],
        microphone: list[dict[str, int | str]],
    ) -> float:
        largest_ticks = 0
        for audio in (desktop, microphone):
            for video_item, audio_item in zip(video, audio):
                largest_ticks = max(
                    largest_ticks,
                    abs(int(video_item["start_qpc"]) - int(audio_item["start_qpc"])),
                    abs(int(video_item["end_qpc"]) - int(audio_item["end_qpc"])),
                )
        error_ms = largest_ticks / 10_000
        if error_ms > 25.0:
            raise RuntimeError(f"音画分段边界偏差 {error_ms:.3f}ms，已拒绝保存")
        return error_ms

    @staticmethod
    def _pin_audio_segments(
        buffer: NativeReplayBuffer,
        destination: Path,
        items: list[dict[str, int | str]],
    ) -> list[Path]:
        pinned_paths = []
        for item in items:
            source = buffer.segments_directory / str(item["file"])
            pinned = destination / str(item["file"])
            try:
                os.link(source, pinned)
            except OSError:
                shutil.copy2(source, pinned)
            pinned_paths.append(pinned)
        return pinned_paths

    @staticmethod
    def _load_manifest(path: Path) -> list[dict[str, int | str]]:
        if not path.is_file():
            return []
        items = []
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                item = json.loads(line)
                if all(key in item for key in ("index", "file", "start_qpc", "end_qpc")):
                    items.append(item)
            except json.JSONDecodeError:
                continue
        return items

    def _flush_input_writer(self, *, timeout: float) -> None:
        thread = self._input_thread
        if thread is None or not thread.is_alive():
            return
        barrier = _WriterBarrier(threading.Event())
        try:
            self._input_queue.put(barrier, timeout=1.0)
        except queue.Full as exc:
            raise RuntimeError("按键日志队列繁忙，暂时无法保存完整时间窗") from exc
        if not barrier.completed.wait(timeout):
            raise TimeoutError("等待按键日志写入磁盘超时")

    def _close_log_locked(self) -> None:
        if self._log_stream is not None:
            self._log_stream.close()
            self._log_stream = None

    def _start_input_writer_locked(self, buffer: NativeReplayBuffer) -> None:
        self._input_dropped = 0
        self._session_monotonic_ns = time.perf_counter_ns()
        self._session_wall_ns = time.time_ns()
        self._input_thread = threading.Thread(
            target=self._write_input_timeline,
            args=(buffer,),
            daemon=True,
            name="replay-input-writer",
        )
        self._input_thread.start()

    def _stop_input_writer_locked(self) -> None:
        thread = self._input_thread
        if thread is None:
            return
        try:
            self._input_queue.put_nowait(None)
        except queue.Full:
            try:
                self._input_queue.get_nowait()
            except queue.Empty:
                pass
            self._input_queue.put_nowait(None)
        thread.join(timeout=3.0)
        self._input_thread = None

    def _write_input_timeline(self, buffer: NativeReplayBuffer) -> None:
        keybinds = load_game_keybinds()
        labels_by_key: dict[str, list[str]] = {}
        for name in KEYBIND_NAMES:
            labels_by_key.setdefault(keybinds.key_for(name), []).append(keybinds.label_for(name))
        process_cache: dict[int, str | None] = {}
        pressed_at: dict[str, int] = {}
        released_at: dict[str, int] = {}
        sequence = 0
        previous_event_ns: int | None = None
        with buffer.events_jsonl.open("w", encoding="utf-8", buffering=1) as jsonl, buffer.events_csv.open(
            "w", encoding="utf-8-sig", newline=""
        ) as csv_stream:
            csv_writer = csv.writer(csv_stream)
            csv_writer.writerow(_CSV_HEADER)
            while True:
                event = self._input_queue.get()
                if event is None:
                    break
                if isinstance(event, _WriterBarrier):
                    jsonl.flush()
                    csv_stream.flush()
                    event.completed.set()
                    continue
                if event.pressed and event.hotkey in pressed_at:
                    continue
                if not event.pressed and event.hotkey not in pressed_at:
                    continue
                process_name = process_cache.get(event.foreground_pid)
                if event.foreground_pid not in process_cache:
                    process_name = _process_basename(event.foreground_pid)
                    process_cache[event.foreground_pid] = process_name
                sequence += 1
                held_ms = None
                released_ms = None
                delta_ms = None if previous_event_ns is None else (event.monotonic_ns - previous_event_ns) / 1_000_000
                previous_event_ns = event.monotonic_ns
                if event.pressed:
                    previous_release = released_at.get(event.hotkey)
                    if previous_release is not None:
                        released_ms = (event.monotonic_ns - previous_release) / 1_000_000
                    pressed_at[event.hotkey] = event.monotonic_ns
                else:
                    previous_press = pressed_at.pop(event.hotkey, None)
                    if previous_press is not None:
                        held_ms = (event.monotonic_ns - previous_press) / 1_000_000
                    released_at[event.hotkey] = event.monotonic_ns
                active_keys = list(pressed_at)
                overlap_keys = [key for key in active_keys if key != event.hotkey]
                relative_ms = (event.monotonic_ns - self._session_monotonic_ns) / 1_000_000
                wall_ns = self._session_wall_ns + event.monotonic_ns - self._session_monotonic_ns
                local_time = datetime.fromtimestamp(wall_ns / 1_000_000_000).strftime("%H:%M:%S:%f")[:-3]
                labels = labels_by_key.get(event.hotkey, [])
                physical_name = physical_input_name(event.hotkey)
                record = {
                    "sequence": sequence,
                    "utc_unix_ns": wall_ns,
                    "local_time": local_time,
                    "monotonic_ns": event.monotonic_ns,
                    "qpc_100ns": event.monotonic_ns // 100,
                    "relative_ms": round(relative_ms, 3),
                    "delta_from_previous_event_ms": None if delta_ms is None else round(delta_ms, 3),
                    "state": "down" if event.pressed else "up",
                    "hotkey": event.hotkey,
                    "physical_name": physical_name,
                    "event_text": physical_event_text(event.hotkey, event.pressed, labels),
                    "vk": event.vk,
                    "action_names": labels,
                    "held_ms": None if held_ms is None else round(held_ms, 3),
                    "released_ms": None if released_ms is None else round(released_ms, 3),
                    "release_gap_ms": None if released_ms is None else round(released_ms, 3),
                    "active_keys_after_event": active_keys,
                    "overlap_keys": overlap_keys,
                    "overlap_count": len(overlap_keys),
                    "foreground_hwnd": event.foreground_hwnd,
                    "foreground_pid": event.foreground_pid,
                    "foreground_process": process_name,
                }
                jsonl.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                csv_writer.writerow(self._record_csv_row(record))
            jsonl.write(json.dumps({"event": "writer_finished", "dropped": self._input_dropped}, ensure_ascii=False) + "\n")

    @staticmethod
    def _read_window_records(path: Path, start_ns: int, end_ns: int) -> list[dict[str, object]]:
        records = []
        if not path.is_file():
            return records
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            monotonic_ns = record.get("monotonic_ns")
            if isinstance(monotonic_ns, int) and start_ns <= monotonic_ns <= end_ns:
                records.append(record)
        records.sort(key=lambda item: (item["monotonic_ns"], item.get("sequence", 0)))
        previous_ns = None
        for index, record in enumerate(records, start=1):
            monotonic_ns = int(record["monotonic_ns"])
            record["sequence"] = index
            record["relative_ms"] = round((monotonic_ns - start_ns) / 1_000_000, 3)
            record["delta_from_previous_event_ms"] = (
                None if previous_ns is None else round((monotonic_ns - previous_ns) / 1_000_000, 3)
            )
            previous_ns = monotonic_ns
        return records

    def _write_session_events(self, session: NativeReplaySession, records: list[dict[str, object]], start_ns: int) -> None:
        with session.events_jsonl.open("w", encoding="utf-8", newline="\n") as jsonl, session.events_csv.open(
            "w", encoding="utf-8-sig", newline=""
        ) as csv_stream:
            writer = csv.writer(csv_stream)
            writer.writerow(_CSV_HEADER)
            for record in records:
                jsonl.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                writer.writerow(self._record_csv_row(record))
            jsonl.write(json.dumps({
                "event": "saved_window_finished",
                "event_count": len(records),
                "window_start_monotonic_ns": start_ns,
                "dropped": self._input_dropped,
            }, ensure_ascii=False) + "\n")

    @staticmethod
    def _record_csv_row(record: dict[str, object]) -> list[object]:
        def milliseconds(key: str) -> str:
            value = record.get(key)
            return "" if value is None else f"{float(value):.3f}"

        return [
            record.get("sequence", ""), record.get("local_time", ""), milliseconds("relative_ms"),
            milliseconds("delta_from_previous_event_ms"), record.get("event_text", ""),
            record.get("physical_name", ""), record.get("hotkey", ""),
            " / ".join(record.get("action_names", [])), milliseconds("held_ms"),
            milliseconds("release_gap_ms"), " / ".join(record.get("active_keys_after_event", [])),
            " / ".join(record.get("overlap_keys", [])), record.get("foreground_process") or "未知",
            record.get("foreground_pid", ""),
        ]

    @staticmethod
    def _read_json_object(path: Path) -> dict[str, object]:
        if not path.is_file():
            return {}
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
            return value if isinstance(value, dict) else {}
        except (OSError, UnicodeError, json.JSONDecodeError):
            return {}


class NativeAudioPreviewController:
    """Run lightweight WASAPI peak monitoring without screen capture or saving audio."""

    def __init__(self) -> None:
        self._process: subprocess.Popen | None = None
        self._temporary: tempfile.TemporaryDirectory | None = None
        self._levels_file: Path | None = None
        self._log_file: Path | None = None
        self._stop_file: Path | None = None
        self._log_stream = None
        self._last_error: str | None = None

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def start(self, settings: ReplaySettings) -> None:
        self.stop()
        executable = native_replay_executable(settings.core_path)
        if executable is None:
            raise RuntimeError("没有找到录像核心，声音设备预检暂不可用")
        temporary = tempfile.TemporaryDirectory(prefix="mapl-audio-preview-")
        root = Path(temporary.name)
        levels_file = root / "audio-levels.json"
        log_file = root / "preview.log"
        stop_file = root / ".stop"
        command = [
            str(executable),
            "--audio-monitor", "true",
            "--stop-file", str(stop_file),
            "--work-directory", str(root / "work"),
            "--audio-levels", str(levels_file),
            "--audio-info", str(root / "audio-info.json"),
            "--microphone-device-id", _wasapi_endpoint_id(settings.microphone_device_id),
            "--microphone-gain-percent", str(settings.microphone_gain_percent),
            "--desktop-gain-percent", str(settings.desktop_gain_percent),
        ]
        log_stream = log_file.open("w", encoding="utf-8", newline="\n")
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=log_stream,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                close_fds=True,
            )
        except Exception:
            log_stream.close()
            temporary.cleanup()
            raise
        self._temporary = temporary
        self._levels_file = levels_file
        self._log_file = log_file
        self._stop_file = stop_file
        self._log_stream = log_stream
        self._process = process
        self._last_error = None

    def audio_levels(self) -> tuple[int, int]:
        path = self._levels_file
        if path is None:
            return 0, 0
        payload = NativeReplayController._read_json_object(path)
        try:
            desktop = max(0, min(100, int(payload.get("desktop", 0))))
            microphone = max(0, min(100, int(payload.get("microphone", 0))))
        except (TypeError, ValueError):
            return 0, 0
        return desktop, microphone

    def poll(self) -> int | None:
        process = self._process
        if process is None:
            return None
        return_code = process.poll()
        if return_code is None:
            return None
        self._close_log()
        if return_code != 0:
            self._last_error = self._read_log_tail() or f"声音设备预检退出码 {return_code}"
        self._process = None
        return return_code

    def stop(self, timeout: float = 5.0) -> int | None:
        process = self._process
        if process is None:
            self._cleanup_temporary()
            return None
        if process.poll() is None and self._stop_file is not None:
            self._stop_file.touch()
        try:
            return_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                return_code = process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                process.kill()
                return_code = process.wait(timeout=2.0)
        self._close_log()
        self._process = None
        self._cleanup_temporary()
        return return_code

    def _read_log_tail(self) -> str | None:
        path = self._log_file
        if path is None or not path.is_file():
            return None
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return None
        return lines[-1] if lines else None

    def _close_log(self) -> None:
        if self._log_stream is not None:
            self._log_stream.close()
            self._log_stream = None

    def _cleanup_temporary(self) -> None:
        temporary = self._temporary
        self._temporary = None
        self._levels_file = None
        self._log_file = None
        self._stop_file = None
        if temporary is not None:
            temporary.cleanup()


def _process_basename(pid: int) -> str | None:
    if pid <= 0 or os.name != "nt":
        return None
    process = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
    if not process:
        return None
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not ctypes.windll.kernel32.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(size)):
            return None
        return Path(buffer.value).name
    finally:
        ctypes.windll.kernel32.CloseHandle(process)


def _wasapi_endpoint_id(identifier: str | None) -> str:
    if not identifier:
        return ""
    try:
        decoded = bytes.fromhex(identifier).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return identifier
    return decoded if decoded.startswith("{") else identifier
