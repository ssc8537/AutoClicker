"""MyAutoPlayer — 键盘自动化序列播放器。

程序入口。启动 PySide6 窗口并注册全局热键。

阶段 1 Hello World 验证：
    运行程序 → 光标放在记事本 → 按 F9 → 自动打出 "Hello World"
"""
import sys
import ctypes
import atexit
import threading
import keyboard

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6.QtCore import QObject, Qt, Signal, Slot

from src.core.input_simulator import type_string
from src.core.hotkey_manager import HotkeyManager, TriggerMode
from src.utils.logger import get_logger, setup_logging
from src.ui.osd_window import OsdPopup

logger = get_logger(__name__)


class _HotkeyDispatcher(QObject):
    """将全局热键钩子线程中的事件安全地转发到 Qt 主线程。"""

    f9_signal = Signal()
    f9_stop_signal = Signal()
    toggle_signal = Signal(bool)

    def __init__(self, status_label: QLabel, osd_popup: OsdPopup):
        super().__init__()
        self._status_label = status_label
        self._osd_popup = osd_popup
        self._execution_lock = threading.Lock()
        self._stop_event: threading.Event | None = None
        self._worker: threading.Thread | None = None
        # 强制排队，避免 QObject 的线程归属导致钩子线程直接调用槽函数。
        self.f9_signal.connect(self._start_f9, Qt.ConnectionType.QueuedConnection)
        self.f9_stop_signal.connect(
            self._stop_f9, Qt.ConnectionType.QueuedConnection
        )
        self.toggle_signal.connect(
            self._apply_global_status, Qt.ConnectionType.QueuedConnection
        )

    def on_f9_hook(self) -> None:
        """供 keyboard 钩子线程调用；仅启动一次按住执行循环。"""
        if not self._execution_lock.acquire(blocking=False):
            logger.debug("F9 按下被丢弃：脚本已经运行")
            return
        try:
            self.f9_signal.emit()
        except Exception:
            # 发信号失败时不能遗留锁，否则之后所有 F9 都会被永久丢弃。
            self._execution_lock.release()
            logger.exception("F9 事件无法转发到 Qt 主线程")

    def on_f9_stop_hook(self) -> None:
        """供 keyboard 钩子线程调用；松开 F9 时请求停止。"""
        self.f9_stop_signal.emit()

    def on_toggle_hook(self, disabled: bool) -> None:
        """供 keyboard 钩子线程调用；实际 UI 更新在 Qt 主线程执行。"""
        self.toggle_signal.emit(disabled)

    @Slot()
    def _start_f9(self) -> None:
        """Qt 主线程创建可取消的 F9 循环，并显示开始提示。"""
        try:
            self._stop_event = threading.Event()
            self._worker = threading.Thread(
                target=self._run_f9_loop,
                args=(self._stop_event,),
                daemon=True,
                name="hello-world-loop",
            )
            self._worker.start()
            logger.info("F9 按下 — Hello World 循环已启动")
            self._osd_popup.show_notification("Hello World 脚本运行中", success=True)
        except Exception:
            logger.exception("F9 循环启动失败")
            self._execution_lock.release()

    def _run_f9_loop(self, stop_event: threading.Event) -> None:
        """后台输入循环；只负责 SendInput，不触碰 Qt UI。"""
        try:
            while not stop_event.is_set():
                if not type_string("Hello World", stop_event=stop_event):
                    break
                # 轮次间隔也可被松开 F9 或 F12 立即中断。
                if stop_event.wait(0.05):
                    break
        except Exception:
            logger.exception("Hello World 循环执行失败")
        finally:
            self._execution_lock.release()

    @Slot()
    def _stop_f9(self) -> None:
        """Qt 主线程中停止 F9 循环，并且只显示一次结束提示。"""
        if self._stop_event is None or self._stop_event.is_set():
            return
        self._stop_event.set()
        logger.info("F9 松开/全局禁用 — Hello World 循环停止")
        self._osd_popup.show_notification("Hello World 脚本已停止", success=False)

    def stop_active_execution(self) -> None:
        """关闭窗口时停止后台输入，避免退出后仍继续发送按键。"""
        if self._stop_event is not None:
            self._stop_event.set()

    @Slot(bool)
    def _apply_global_status(self, disabled: bool) -> None:
        """Qt 主线程中更新安全开关的可视状态。"""
        if disabled:
            self._status_label.setText("🔴 热键已禁用")
            self._status_label.setStyleSheet(
                "font-size: 20px; color: red; font-weight: bold;"
            )
        else:
            self._status_label.setText("🟢 热键已启用")
            self._status_label.setStyleSheet(
                "font-size: 20px; color: green; font-weight: bold;"
            )


class MainWindow(QMainWindow):
    """主窗口 — 阶段 1 仅显示状态提示。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyAutoPlayer — 键盘自动化序列播放器")
        self.resize(600, 400)
        self._hotkey_mgr = None
        self._setup_ui()
        self._osd_popup = OsdPopup(None)
        self._dispatcher = _HotkeyDispatcher(self._status_label, self._osd_popup)
        self._setup_hotkey()

    def _setup_ui(self):
        """初始化最小 UI。"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 阶段1.0 安全机制：状态指示标签
        self._status_label = QLabel("🔴 热键已禁用")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("font-size: 20px; color: red; font-weight: bold;")
        layout.addWidget(self._status_label)

        info = QLabel("MyAutoPlayer 已启动\n\n按 F12 启用/禁用热键\n按住 F9 循环打出 Hello World，松开停止\n（鼠标不要在程序窗口内）")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("font-size: 16px; color: #333;")
        layout.addWidget(info)

    def _setup_hotkey(self):
        """注册全局热键 F9。"""
        hwnd = int(self.winId())
        self._hotkey_mgr = HotkeyManager(hwnd)

        # 注册 F9 热键
        self._hotkey_mgr.register(
            "f9",
            self._dispatcher.on_f9_hook,
            mode=TriggerMode.DOWN,
            stop_callback=self._dispatcher.on_f9_stop_hook,
        )

        # 阶段1.0 安全机制：全局启用/禁用键 F12 + 状态通知
        self._hotkey_mgr.set_global_disable_key("f12")
        self._hotkey_mgr.on_toggle(self._dispatcher.on_toggle_hook)

        self._hotkey_mgr.start()
        logger.info("热键管理器已启动，F9 已注册，F12 为全局启用/禁用键")

    def closeEvent(self, event):
        """窗口关闭时停止热键监听。"""
        logger.info("程序退出")
        keyboard.unhook_all()  # 第一道防线：显式释放全局钩子
        if self._hotkey_mgr:
            self._hotkey_mgr.stop()
        self._dispatcher.stop_active_execution()
        if self._osd_popup:
            self._osd_popup.close()
        super().closeEvent(event)


def _cleanup():
    """进程退出兜底清理（atexit 注册）。第二道防线。"""
    try:
        keyboard.unhook_all()
    except Exception:
        pass


atexit.register(_cleanup)


def main():
    setup_logging()
    logger.info("MyAutoPlayer 启动")

    app = QApplication(sys.argv)

    # 检测管理员权限（部分游戏需要以管理员权限运行 SendInput 才能生效）
    if not _is_admin():
        logger.warning("当前未以管理员权限运行，某些游戏可能无法接收模拟输入")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


def _is_admin() -> bool:
    """检测是否以管理员权限运行。"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


if __name__ == "__main__":
    main()
