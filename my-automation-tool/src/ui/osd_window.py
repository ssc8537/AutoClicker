"""OSD浮层窗口 — 在屏幕顶部居中显示提示文本。

参考 Quickinput PopsUi.cpp 的全局 Overlay 窗口设计。
用 PySide6 创建无边框、透明背景、置顶浮层。
"""
import json
from pathlib import Path

from src.utils.app_paths import config_root

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QApplication, QGraphicsDropShadowEffect


class OsdPopup(QWidget):
    """屏幕提示文本浮层窗口，脚本执行/结束时在屏幕顶部居中显示提示。"""

    _SETTINGS_PATH = config_root() / "settings.json"

    def __init__(self, parent=None):
        # OSD 是全局工具浮层，不能依附主窗口，否则会随主窗口层级和生命周期变化。
        super().__init__(None)
        self._setup_window_flags()
        self._load_config()
        self.setFixedSize(400, 60)
        self._setup_ui()
        self._setup_animation()

    def _setup_window_flags(self):
        """配置窗口标志：无边框 + 置顶 + 工具窗口（不在任务栏显示）。"""
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

    def _load_config(self):
        """从 settings.json 加载OSD配置，失败时用默认值。"""
        self.popup_enabled = True
        self.popup_y = 10
        self.popup_size = 24
        self.popup_duration_ms = 2000
        self.popup_success_color = "#00FF00"
        self.popup_end_color = "#FF0000"
        try:
            if self._SETTINGS_PATH.exists():
                with open(self._SETTINGS_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.popup_enabled = cfg.get("popup_enabled", True)
                self.popup_y = cfg.get("popup_position_y", 10)
                self.popup_size = cfg.get("popup_size", 24)
                self.popup_duration_ms = cfg.get("popup_duration_ms", 2000)
                self.popup_success_color = cfg.get("popup_success_color", "#00FF00")
                self.popup_end_color = cfg.get("popup_end_color", "#FF0000")
        except Exception:
            pass

    def _setup_ui(self):
        """初始化标签和阴影效果。"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setFont(QFont("Microsoft YaHei", self.popup_size, QFont.Bold))
        self._label.setStyleSheet(
            f"color: {self.popup_success_color}; background: transparent;"
        )
        layout.addWidget(self._label)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 160))
        self._label.setGraphicsEffect(shadow)

    def _setup_animation(self):
        """初始化淡出动画和自动隐藏定时器。"""
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(500)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_anim.finished.connect(self.hide)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._start_fade_out)

    def show_notification(self, text: str, success: bool = True):
        """显示提示文本，停留后自动淡出。

        Args:
            text: 要显示的文本
            success: True 用成功颜色（绿），False 用结束颜色（红）
        """
        if not self.popup_enabled:
            return

        # 更新文本和颜色
        self._label.setText(text)
        color = self.popup_success_color if success else self.popup_end_color
        self._label.setStyleSheet(
            f"color: {color}; background: transparent;"
        )

        # 重置位置（响应屏幕分辨率变化）
        self.update_position()

        # 重置动画状态
        self._hide_timer.stop()
        self._fade_anim.stop()
        self.setWindowOpacity(1.0)

        # 显示并置顶
        self.show()
        self.raise_()

        # 启动自动隐藏计时
        self._hide_timer.start(self.popup_duration_ms)

    def _start_fade_out(self):
        """执行淡出动画。"""
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.start()

    def update_position(self):
        """移动到屏幕顶部居中位置。"""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = geo.left() + (geo.width() - self.width()) // 2
        y = geo.top() + self.popup_y
        self.move(x, y)

    def mousePressEvent(self, event):
        """点击穿透保护：点击OSD不传递给下层窗口。"""
        event.accept()
