"""案例对齐的一排快捷连点：即时保存、可中断、无忙等循环。"""
from __future__ import annotations

import json
import os
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.core.input_keys import MOUSE_BUTTON_FOR_HOTKEY, MOUSE_HOTKEYS, normalise_input_key
from src.core.input_simulator import mouse_down, mouse_up, press_key, release_key
from src.utils.app_paths import config_root
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class QuickClickSettings:
    enabled: bool = False
    hotkey: str = "mouse_left"
    mode: str = "down"
    interval_ms: int = 200

    def validated(self) -> "QuickClickSettings":
        hotkey = normalise_input_key(self.hotkey)
        if self.mode not in {"down", "switch"}:
            raise ValueError("快捷连点模式必须是 down 或 switch")
        if (
            isinstance(self.interval_ms, bool)
            or not isinstance(self.interval_ms, int)
            or not 1 <= self.interval_ms <= 10000
        ):
            raise ValueError("快捷连点间隔必须是 1 至 10000 毫秒")
        return QuickClickSettings(bool(self.enabled), hotkey, self.mode, self.interval_ms)


class QuickClickSettingsStore:
    def __init__(self, path: Path | None = None):
        self.path = path or (config_root() / "quick_click.json")

    def load(self) -> QuickClickSettings:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("配置根节点必须是对象")
            return QuickClickSettings(
                enabled=data.get("enabled", False),
                hotkey=data.get("hotkey", "mouse_left"),
                mode=data.get("mode", "down"),
                interval_ms=data.get("interval_ms", 200),
            ).validated()
        except FileNotFoundError:
            return QuickClickSettings()
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            logger.warning("快捷连点配置无效，使用安全默认值：%s", exc)
            return QuickClickSettings()

    def save(self, settings: QuickClickSettings) -> QuickClickSettings:
        settings = settings.validated()
        temporary_name = None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self.path.name}.", dir=self.path.parent, text=True
            )
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as temporary:
                json.dump(
                    {
                        "enabled": settings.enabled,
                        "hotkey": settings.hotkey,
                        "mode": settings.mode,
                        "interval_ms": settings.interval_ms,
                    },
                    temporary,
                    ensure_ascii=False,
                    indent=2,
                )
                temporary.write("\n")
            os.replace(temporary_name, self.path)
            return settings
        except (OSError, UnicodeError):
            if temporary_name is not None:
                Path(temporary_name).unlink(missing_ok=True)
            raise


class QuickClickController:
    """一个受控 worker；所有等待都能被 stop_event 立即唤醒。"""

    def __init__(self, on_finished: Callable[[int], None] | None = None):
        self._on_finished = on_finished
        self._lock = threading.RLock()
        self._settings = QuickClickSettings()
        self._generation = 0
        self._desired_running = False
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def configure(self, settings: QuickClickSettings) -> None:
        settings = settings.validated()
        self.shutdown()
        with self._lock:
            self._settings = settings
            self._generation = 0
            self._desired_running = False
            self._stop_event = threading.Event()

    def start(self, generation: int) -> None:
        with self._lock:
            if generation < self._generation:
                return
            self._generation = generation
            self._desired_running = True
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event = threading.Event()
            settings = self._settings
            self._thread = threading.Thread(
                target=self._run,
                args=(settings, generation, self._stop_event),
                daemon=True,
                name="quick-click",
            )
            self._thread.start()

    def stop(self, generation: int) -> None:
        with self._lock:
            if generation < self._generation:
                return
            self._generation = generation
            self._desired_running = False
            self._stop_event.set()

    def is_running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def shutdown(self) -> None:
        with self._lock:
            generation = self._generation + 1
            thread = self._thread
        self.stop(generation)
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)

    def _run(
        self, settings: QuickClickSettings, generation: int, stop_event: threading.Event
    ) -> None:
        press, release = self._input_functions(settings.hotkey)
        pressed = False
        try:
            hold_ms = min(20, max(1, settings.interval_ms // 2))
            rest_ms = max(0, settings.interval_ms - hold_ms)
            while not stop_event.is_set():
                press()
                pressed = True
                if stop_event.wait(hold_ms / 1000.0):
                    break
                release()
                pressed = False
                if rest_ms and stop_event.wait(rest_ms / 1000.0):
                    break
        except Exception:
            logger.exception("快捷连点执行失败")
        finally:
            if pressed:
                try:
                    release()
                except Exception:
                    logger.exception("快捷连点释放按键失败")
            restart = False
            with self._lock:
                if self._thread is threading.current_thread():
                    self._thread = None
                restart = self._desired_running and self._generation > generation
                restart_generation = self._generation
            if self._on_finished is not None:
                self._on_finished(generation)
            if restart:
                self.start(restart_generation)

    @staticmethod
    def _input_functions(hotkey: str) -> tuple[Callable[[], None], Callable[[], None]]:
        if hotkey in MOUSE_HOTKEYS:
            button = MOUSE_BUTTON_FOR_HOTKEY[hotkey]
            return lambda: mouse_down(button), lambda: mouse_up(button)
        return lambda: press_key(hotkey), lambda: release_key(hotkey)
