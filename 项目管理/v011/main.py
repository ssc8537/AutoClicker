"""MyAutoPlayer — 键盘自动化序列播放器。

程序入口。启动 PySide6 窗口并注册全局热键。

阶段 1 Hello World 验证：
    运行程序 → 光标放在记事本 → 按 F9 → 自动打出 "Hello World"
"""
import sys
import ctypes
import atexit
import keyboard

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from src.core.input_simulator import type_string
from src.core.hotkey_manager import HotkeyManager, TriggerMode
from src.utils.logger import get_logger, setup_logging
from src.ui.osd_window import OsdPopup

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """主窗口 — 阶段 1 仅显示状态提示。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyAutoPlayer — 键盘自动化序列播放器")
        self.resize(600, 400)
        self._hotkey_mgr = None
        self._setup_ui()
        self._setup_hotkey()
        self._osd_popup = OsdPopup(self)

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

        info = QLabel("MyAutoPlayer 已启动\n\n按 F12 启用热键\n按 F9 在记事本中打出 Hello World\n（鼠标不要在程序窗口内）")
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
            self._on_f9_pressed,
            mode=TriggerMode.PRESS,
        )

        # 阶段1.0 安全机制：全局启用/禁用键 F12 + 状态通知
        self._hotkey_mgr.set_global_disable_key("f12")
        self._hotkey_mgr.on_toggle(self._update_global_status)

        self._hotkey_mgr.start()
        logger.info("热键管理器已启动，F9 已注册，F12 为全局启用/禁用键")

    def _update_global_status(self, disabled: bool):
        """更新状态指示标签颜色和文字。"""
        if disabled:
            self._status_label.setText("🔴 热键已禁用")
            self._status_label.setStyleSheet("font-size: 20px; color: red; font-weight: bold;")
        else:
            self._status_label.setText("🟢 热键已启用")
            self._status_label.setStyleSheet("font-size: 20px; color: green; font-weight: bold;")

    def _on_f9_pressed(self):
        """F9 热键回调：在焦点窗口打出 Hello World。"""
        logger.info("F9 触发 — 执行 Hello World")
        type_string("Hello World")
        self._osd_popup.show_notification("Hello World 脚本执行成功", success=True)

    def closeEvent(self, event):
        """窗口关闭时停止热键监听。"""
        logger.info("程序退出")
        keyboard.unhook_all()  # 第一道防线：显式释放全局钩子
        if self._hotkey_mgr:
            self._hotkey_mgr.stop()
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
