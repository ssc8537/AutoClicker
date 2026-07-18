"""Stage 4T 的自有窗口标题栏、垂直缩放把手与系统托盘控制。"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QAction, QIcon, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QStyle,
    QSystemTrayIcon,
    QToolButton,
    QWidget,
)


def application_icon() -> QIcon:
    """返回窗口和托盘共用的自有粉色应用图标。"""
    asset_path = Path(__file__).resolve().parents[2] / "assets" / "myautoplayer-pink.svg"
    return QIcon(str(asset_path))


class WindowTitleBar(QWidget):
    """不复制案例资源的三动作自有标题栏。"""

    minimize_requested = Signal()
    hide_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("window_title_bar")
        self.setFixedHeight(36)
        self._drag_origin: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 6, 0)
        layout.setSpacing(6)
        title = QLabel("我的自动播放器")
        title.setObjectName("window_title_label")
        layout.addWidget(title)
        layout.addStretch(1)

        self._hide_button = self._make_button("藏", "隐藏到系统托盘", "window_hide_button")
        self._minimize_button = self._make_button("—", "最小化到任务栏", "window_minimize_button")
        self._close_button = self._make_button("×", "退出程序", "window_close_button")
        layout.addWidget(self._hide_button)
        layout.addWidget(self._minimize_button)
        layout.addWidget(self._close_button)
        self._hide_button.clicked.connect(self.hide_requested)
        self._minimize_button.clicked.connect(self.minimize_requested)
        self._close_button.clicked.connect(self.close_requested)

    @staticmethod
    def _make_button(text: str, tooltip: str, object_name: str) -> QToolButton:
        button = QToolButton()
        button.setObjectName(object_name)
        button.setText(text)
        button.setToolTip(tooltip)
        button.setFixedSize(26, 26)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    def set_hide_available(self, available: bool) -> None:
        self._hide_button.setEnabled(available)
        if not available:
            self._hide_button.setToolTip("系统托盘不可用，无法隐藏")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = event.globalPosition().toPoint()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            window = self.window()
            current = event.globalPosition().toPoint()
            window.move(window.pos() + current - self._drag_origin)
            self._drag_origin = current
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = None
        super().mouseReleaseEvent(event)


class VerticalResizeHandle(QWidget):
    """固定宽度窗口的底边垂直缩放把手。"""

    def __init__(self, window: QMainWindow):
        super().__init__(window)
        self.setObjectName("vertical_resize_handle")
        self.setFixedHeight(6)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self._window = window
        self._origin_y: int | None = None
        self._origin_height = 0

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin_y = event.globalPosition().toPoint().y()
            self._origin_height = self._window.height()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._origin_y is not None and event.buttons() & Qt.MouseButton.LeftButton:
            requested_height = self._origin_height + event.globalPosition().toPoint().y() - self._origin_y
            bounded_height = max(
                self._window.minimumHeight(),
                min(requested_height, self._window.maximumHeight()),
            )
            self._window.resize(self._window.width(), bounded_height)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin_y = None
        super().mouseReleaseEvent(event)


class WindowChromeController:
    """标题栏和托盘都只调用既有窗口/F12 生命周期，不新建状态机。"""

    def __init__(
        self,
        window: QMainWindow,
        tray_available: Callable[[], bool] = QSystemTrayIcon.isSystemTrayAvailable,
    ):
        self._window = window
        self._tray_available = tray_available
        self.tray: QSystemTrayIcon | None = None
        self.menu: QMenu | None = None

    def install(self, title_bar: WindowTitleBar) -> None:
        title_bar.minimize_requested.connect(self.minimize_window)
        title_bar.hide_requested.connect(self.hide_window)
        title_bar.close_requested.connect(self.exit_program)
        if self._tray_available():
            self._create_tray()
        else:
            title_bar.set_hide_available(False)

    def _create_tray(self) -> None:
        self.tray = QSystemTrayIcon(self._window)
        icon = self._window.windowIcon()
        if icon.isNull():
            icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray.setIcon(icon)
        self.tray.setToolTip(self._window.windowTitle())
        self.menu = QMenu(self._window)
        show_action = QAction("显示主窗口", self.menu)
        hide_action = QAction("隐藏主窗口", self.menu)
        exit_action = QAction("退出程序", self.menu)
        show_action.triggered.connect(self.show_window)
        hide_action.triggered.connect(self.hide_window)
        exit_action.triggered.connect(self.exit_program)
        self.menu.addActions((show_action, hide_action, exit_action))
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def minimize_window(self) -> None:
        self._window.showMinimized()

    def hide_window(self) -> None:
        if self.tray is not None:
            self._window.hide()

    def show_window(self) -> None:
        self._window.showNormal()
        self._window.raise_()
        self._window.activateWindow()

    def exit_program(self) -> None:
        self._window.close()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()
