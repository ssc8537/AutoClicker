"""单实例、可中断的物理键盘序列播放器。"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable, Sequence

from src.core.input_simulator import press_key, release_key
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class KeyTapStep:
    """一次物理按下、释放及释放后等待。"""

    key: str
    hold_ms: int
    delay_ms: int


class SequencePlayer:
    """在后台播放一个键盘序列；同一时刻只允许一个运行实例。"""

    def __init__(
        self,
        press: Callable[[str], None] = press_key,
        release: Callable[[str], None] = release_key,
        on_finished: Callable[[], None] | None = None,
    ):
        self._press = press
        self._release = release
        self._on_finished = on_finished
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @staticmethod
    def delay_seconds(delay_ms: int, speed: float) -> float:
        """返回倍率缩放后的释放后等待时间。"""
        return delay_ms / speed / 1000.0

    def play(
        self, steps: Sequence[KeyTapStep], count: int, speed: float
    ) -> bool:
        """异步开始播放。已运行时返回 False，绝不创建第二个播放器。"""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                logger.warning("拒绝启动序列：已有序列正在运行")
                return False
            self._stop_event = threading.Event()
            self._thread = threading.Thread(
                target=self._run,
                args=(tuple(steps), count, speed, self._stop_event),
                daemon=True,
                name="sequence-player",
            )
            self._thread.start()
        return True

    def stop(self) -> None:
        """请求停止；工作线程负责释放正在保持的按键。"""
        self._stop_event.set()

    def is_running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def join(self, timeout: float | None = None) -> None:
        """仅供测试和受控关闭等待播放器结束。"""
        with self._lock:
            thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout)

    def _run(
        self,
        steps: tuple[KeyTapStep, ...],
        count: int,
        speed: float,
        stop_event: threading.Event,
    ) -> None:
        completed = 0
        try:
            while count == 0 or completed < count:
                if stop_event.is_set() or not self._run_once(steps, speed, stop_event):
                    return
                completed += 1
        except Exception:
            logger.exception("键盘序列执行失败")
        finally:
            logger.info("键盘序列结束：已完成 %s 轮", completed)
            callback = self._on_finished
            if callback is not None:
                try:
                    callback()
                except Exception:
                    logger.exception("序列结束回调失败")

    def _run_once(
        self,
        steps: tuple[KeyTapStep, ...],
        speed: float,
        stop_event: threading.Event,
    ) -> bool:
        for step in steps:
            if stop_event.is_set():
                return False
            pressed = False
            try:
                self._press(step.key)
                pressed = True
                if stop_event.wait(step.hold_ms / 1000.0):
                    return False
            finally:
                if pressed:
                    self._release(step.key)
            if stop_event.wait(self.delay_seconds(step.delay_ms, speed)):
                return False
        return True
