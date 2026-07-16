"""MyAutoPlayer 程序入口：阶段 2 的单 JSON 键盘测试宏。"""
from __future__ import annotations

import atexit
import ctypes
import sys
from pathlib import Path

import keyboard
from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

from src.core.hotkey_manager import HotkeyManager, TriggerMode
from src.core.macro_loader import MacroValidationError, TestMacro, load_test_macro
from src.core.sequence_player import SequencePlayer
from src.ui.osd_window import OsdPopup
from src.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)
_MACRO_PATH = Path(__file__).resolve().parent / "config" / "hello_world_macro.json"
_INSTRUCTION_TEXT = (
    "MyAutoPlayer 已启动\n\n按 F12 启用/禁用热键\n"
    "轻按 F9 完整输出一次 hello world\n"
    "（鼠标不要在程序窗口内）"
)


def global_status_notification(disabled: bool) -> tuple[str, bool]:
    """返回全局开关 OSD 的文本和颜色状态。"""
    if disabled:
        return "全局脚本已禁用", False
    return "全局脚本已就绪", True


class _HotkeyDispatcher(QObject):
    """在 Qt 主线程协调热键、OSD 和后台序列播放器。"""

    f9_signal = Signal()
    f9_stop_signal = Signal()
    toggle_signal = Signal(bool)
    player_finished_signal = Signal()

    def __init__(self, status_label: QLabel, osd_popup: OsdPopup, macro: TestMacro):
        super().__init__()
        self._status_label = status_label
        self._osd_popup = osd_popup
        self._macro = macro
        self._player = SequencePlayer(on_finished=self._on_player_finished_worker)
        self._on_natural_finish = None
        self._execution_active = False
        self.f9_signal.connect(self._start_f9, Qt.ConnectionType.QueuedConnection)
        self.f9_stop_signal.connect(self._stop_f9, Qt.ConnectionType.QueuedConnection)
        self.toggle_signal.connect(self._apply_global_status, Qt.ConnectionType.QueuedConnection)
        self.player_finished_signal.connect(
            self._on_player_finished, Qt.ConnectionType.QueuedConnection
        )

    def set_natural_finish_callback(self, callback) -> None:
        self._on_natural_finish = callback

    def on_f9_hook(self) -> None:
        """仅由 keyboard 钩子线程调用。"""
        self.f9_signal.emit()

    def on_f9_stop_hook(self) -> None:
        """仅由 keyboard 钩子线程调用。"""
        self.f9_stop_signal.emit()

    def on_toggle_hook(self, disabled: bool) -> None:
        """仅由 keyboard 钩子线程调用。"""
        self.toggle_signal.emit(disabled)

    def _on_player_finished_worker(self) -> None:
        """播放器线程仅转发信号，绝不直接触碰 Qt 控件。"""
        self.player_finished_signal.emit()

    @Slot()
    def _start_f9(self) -> None:
        if not self._player.play(self._macro.steps, self._macro.count, self._macro.speed):
            logger.info("F9 启动被忽略：测试宏已经运行")
            return
        self._execution_active = True
        logger.info("F9 启动 JSON 测试宏：%s", self._macro.name)
        self._osd_popup.show_notification("hello world 宏运行中", success=True)

    @Slot()
    def _stop_f9(self) -> None:
        self._player.stop()
        if not self._execution_active:
            return
        self._execution_active = False
        logger.info("F9 松开/全局禁用 — JSON 测试宏停止")
        self._osd_popup.show_notification("hello world 宏已停止", success=False)

    @Slot()
    def _on_player_finished(self) -> None:
        if self._on_natural_finish is not None:
            self._on_natural_finish()
        if self._execution_active:
            self._execution_active = False
            logger.info("JSON 测试宏自然结束")
            self._osd_popup.show_notification("hello world 宏已停止", success=False)

    def stop_active_execution(self) -> None:
        self._player.stop()
        self._player.join(timeout=1.0)

    @Slot(bool)
    def _apply_global_status(self, disabled: bool) -> None:
        notification, success = global_status_notification(disabled)
        if disabled:
            self._status_label.setText("🔴 热键已禁用")
            self._status_label.setStyleSheet("font-size: 20px; color: red; font-weight: bold;")
        else:
            self._status_label.setText("🟢 热键已启用")
            self._status_label.setStyleSheet("font-size: 20px; color: green; font-weight: bold;")
        self._osd_popup.show_notification(notification, success=success)


class MainWindow(QMainWindow):
    """阶段 2 仍只保留安全状态提示，不新增配置 UI。"""

    def __init__(self, macro: TestMacro):
        super().__init__()
        self.setWindowTitle("MyAutoPlayer — 键盘自动化序列播放器")
        self.resize(600, 400)
        self._macro = macro
        self._hotkey_mgr: HotkeyManager | None = None
        self._setup_ui()
        self._osd_popup = OsdPopup(None)
        self._dispatcher = _HotkeyDispatcher(self._status_label, self._osd_popup, macro)
        self._setup_hotkey()

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self._status_label = QLabel("🔴 热键已禁用")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("font-size: 20px; color: red; font-weight: bold;")
        layout.addWidget(self._status_label)
        info = QLabel(_INSTRUCTION_TEXT)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("font-size: 16px; color: #333;")
        layout.addWidget(info)

    def _setup_hotkey(self) -> None:
        self._hotkey_mgr = HotkeyManager(int(self.winId()))
        self._hotkey_mgr.register(
            "f9",
            self._dispatcher.on_f9_hook,
            mode=TriggerMode[self._macro.mode.upper()],
            stop_callback=self._dispatcher.on_f9_stop_hook,
            stop_on_release=self._macro.count == 0,
        )
        self._hotkey_mgr.set_global_disable_key("f12")
        self._hotkey_mgr.on_toggle(self._dispatcher.on_toggle_hook)
        self._dispatcher.set_natural_finish_callback(
            lambda: self._hotkey_mgr.mark_finished("f9")
        )
        self._hotkey_mgr.start()
        logger.info("阶段 2 JSON 宏已加载：F9=%s，F12=全局启停", self._macro.mode)

    def closeEvent(self, event) -> None:
        logger.info("程序退出")
        if self._dispatcher:
            self._dispatcher.stop_active_execution()
        keyboard.unhook_all()
        if self._hotkey_mgr:
            self._hotkey_mgr.stop()
        if self._osd_popup:
            self._osd_popup.close()
        super().closeEvent(event)


def _cleanup() -> None:
    try:
        keyboard.unhook_all()
    except Exception:
        pass


atexit.register(_cleanup)


def _is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def main() -> int:
    setup_logging()
    logger.info("MyAutoPlayer 启动")
    try:
        macro = load_test_macro(_MACRO_PATH)
    except MacroValidationError:
        logger.exception("阶段 2 JSON 测试宏无效；为安全起见不注册热键")
        return 1

    app = QApplication(sys.argv)
    if not _is_admin():
        logger.warning("当前未以管理员权限运行，某些游戏可能无法接收模拟输入")
    window = MainWindow(macro)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
