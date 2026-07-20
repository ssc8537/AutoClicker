"""单实例、可中断的脚本轮次播放器。"""
from __future__ import annotations

import threading
from collections.abc import Callable

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SequencePlayer:
    """在后台重复执行一轮脚本；同一时刻只允许一个实例。"""

    def __init__(self, on_finished: Callable[[], None] | None = None):
        self._on_finished = on_finished
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def play(
        self,
        run_once: Callable[[threading.Event], bool],
        count: int,
        *,
        run_id: int | None = None,
    ) -> bool:
        """异步开始执行；run_once 返回 False 时立即停止后续轮次。"""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                logger.warning("拒绝启动脚本：已有脚本正在运行")
                return False
            self._stop_event = threading.Event()
            self._thread = threading.Thread(
                target=self._run,
                args=(run_once, count, self._stop_event, run_id),
                daemon=True,
                name="sequence-player",
            )
            self._thread.start()
        return True

    def stop(self) -> None:
        """请求停止；脚本 player 负责释放正在保持的按键。"""
        self._stop_event.set()

    def is_running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def join(self, timeout: float | None = None) -> None:
        with self._lock:
            thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout)

    def _run(
        self,
        run_once: Callable[[threading.Event], bool],
        count: int,
        stop_event: threading.Event,
        run_id: int | None,
    ) -> None:
        completed = 0
        try:
            while count == 0 or completed < count:
                if stop_event.is_set() or not run_once(stop_event):
                    return
                completed += 1
        except Exception:
            logger.exception("Python 脚本执行失败")
        finally:
            logger.info("Python 脚本结束：已完成 %s 轮", completed)
            if self._on_finished is not None:
                try:
                    if run_id is None:
                        self._on_finished()
                    else:
                        self._on_finished(run_id)
                except Exception:
                    logger.exception("脚本结束回调失败")
